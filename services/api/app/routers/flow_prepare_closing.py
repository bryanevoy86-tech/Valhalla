# services/api/app/routers/flow_prepare_closing.py

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.dependencies import require_prime_control_key
from app.leads.models import Lead
from app.models.deal import Deal
from app.models.match import Buyer, DealBrief
from app.services.deal_context import latest_offer, linked_brief
from app.services.freeze_events import get_deal_freezes
from app.schemas.closing_context import (
    ClosingContext,
    DealSummary,
    FreezeSummary,
    LeadSummary,
    UnderwritingSummary,
)
from app.schemas.flows_lead_to_deal import BuyerMatchCandidate
from app.routers.flow_lead_to_deal import _score_buyer_for_deal  # reuse matcher

router = APIRouter(
    prefix="/flow",
    tags=["Flow", "ClosingContext"],
    dependencies=[Depends(require_prime_control_key)],
)


def _find_top_buyers(
    db: Session,
    deal_brief: Optional[DealBrief],
    min_score: float = 0.5,
    max_results: int = 10,
) -> List[BuyerMatchCandidate]:
    if deal_brief is None:
        return []

    buyers = db.query(Buyer).filter(Buyer.active.is_(True)).all()
    candidates: List[BuyerMatchCandidate] = []

    for buyer in buyers:
        candidate = _score_buyer_for_deal(buyer, deal_brief)
        if candidate is None:
            continue
        if candidate.score < min_score:
            continue
        candidates.append(candidate)

    candidates.sort(key=lambda c: c.score, reverse=True)
    return candidates[:max_results]


@router.get(
    "/closing_context/{backend_deal_id}",
    response_model=ClosingContext,
    status_code=status.HTTP_200_OK,
    summary="Prepare closing context for a deal",
    description=(
        "Builds a unified closing context for a given backend Deal:\n"
        "- lead summary\n"
        "- deal + DealBrief summary\n"
        "- freeze status\n"
        "- simple underwriting summary\n"
        "- top buyer candidates\n"
        "This is what the closer engine / Heimdall can use to start a "
        "closing/negotiation conversation."
    ),
)
def get_closing_context(
    backend_deal_id: int,
    db: Session = Depends(get_db),
) -> ClosingContext:
    # 1. Load backend Deal
    backend_deal: Optional[Deal] = (
        db.query(Deal)
        .filter(Deal.id == backend_deal_id)
        .first()
    )
    if backend_deal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deal with id {backend_deal_id} not found.",
        )

    lead = db.get(Lead, backend_deal.lead_id)
    if lead is None:
        raise HTTPException(status_code=409, detail="Linked lead unavailable")
    brief = linked_brief(db, backend_deal_id)
    offer = latest_offer(db, backend_deal_id)
    events = get_deal_freezes(db, backend_deal_id)
    active = next((item for item in events if not item.is_completed), None)
    latest = active or next(iter(events), None)
    lead_summary = LeadSummary(
        id=lead.id, name=lead.lead_name, email=lead.lead_email, phone=lead.lead_phone,
        source=lead.source, address=lead.property_address, tags=None,
    )
    deal_summary = DealSummary(
        backend_deal_id=backend_deal_id, deal_brief_id=brief.id if brief else None,
        status=backend_deal.status, headline=backend_deal.title,
        region=brief.region if brief else None, property_type=brief.property_type if brief else None,
        price=brief.price if brief else None, arv=backend_deal.arv,
        repairs=backend_deal.estimated_repair_cost, offer=offer.offer_price if offer else None,
        mao=backend_deal.max_allowable_offer, notes=brief.notes if brief else None,
    )
    freeze_summary = FreezeSummary(
        has_freeze=active is not None, count=len(events),
        severity=latest.severity if latest else None,
        reason=(latest.reason or latest.notes) if latest else None,
    )
    uw_summary = UnderwritingSummary(
        ltv=(offer.offer_price / backend_deal.arv) if offer and backend_deal.arv and backend_deal.arv > 0 else None,
        notes=backend_deal.notes,
    )
    buyers = _find_top_buyers(db, brief)
    if active:
        opening = "Review the open policy freeze and its evidence before discussing any offer."
    else:
        opening = "Confirm the seller's timeline and verify the property and pricing assumptions before discussing terms."

    return ClosingContext(
        lead=lead_summary,
        deal=deal_summary,
        buyers=buyers,
        freeze=freeze_summary,
        underwriting=uw_summary,
        suggested_opening=opening,
    )
