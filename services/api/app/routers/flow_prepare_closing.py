# services/api/app/routers/flow_prepare_closing.py

from __future__ import annotations

from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.deal import Deal
from app.models.match import Buyer, DealBrief
from app.models.freeze_events import FreezeEvent
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
)


def _get_latest_freeze_for_deal(
    db: Session,
    backend_deal_id: int,
) -> FreezeSummary:
    """
    Pull latest freeze event for this deal, if any.
    Assumes Postgres JSONB for payload["backend_deal_id"], but will
    gracefully return no-freeze if that fails on SQLite/dev.
    """
    try:
        events: List[FreezeEvent] = (
            db.query(FreezeEvent)
            .filter(
                FreezeEvent.payload["backend_deal_id"].as_integer()
                == backend_deal_id
            )
            .order_by(FreezeEvent.created_at.desc())
            .all()
        )
    except Exception:
        # Fallback for dev / SQLite where JSONB expressions may not work.
        events = []

    if not events:
        return FreezeSummary(
            has_freeze=False,
            severity=None,
            reason=None,
            count=0,
        )

    latest = events[0]
    return FreezeSummary(
        has_freeze=True,
        severity=latest.severity,
        reason=latest.reason,
        count=len(events),
    )


def _build_lead_summary(deal: Deal) -> LeadSummary:
    lead_obj = getattr(deal, "lead", None)
    if lead_obj is None:
        return LeadSummary(
            id=0,
            name="Unknown Lead",
            email=None,
            phone=None,
            source=None,
            address=None,
            tags=None,
        )

    return LeadSummary(
        id=lead_obj.id,
        name=getattr(lead_obj, "name", "") or "Unknown Lead",
        email=getattr(lead_obj, "email", None),
        phone=getattr(lead_obj, "phone", None),
        source=getattr(lead_obj, "source", None),
        address=getattr(lead_obj, "address", None),
        tags=getattr(lead_obj, "tags", None),
    )


def _build_deal_summary(
    backend_deal: Deal,
    deal_brief: Optional[DealBrief],
) -> DealSummary:
    headline = getattr(deal_brief, "headline", None) if deal_brief else None
    region = getattr(deal_brief, "region", None) if deal_brief else None
    property_type = getattr(deal_brief, "property_type", None) if deal_brief else None
    notes = getattr(deal_brief, "notes", None) if deal_brief else None

    return DealSummary(
        backend_deal_id=backend_deal.id,
        deal_brief_id=deal_brief.id if deal_brief else None,
        status=backend_deal.status,
        headline=headline,
        region=region,
        property_type=property_type,
        price=Decimal(str(backend_deal.price))
        if getattr(backend_deal, "price", None) is not None
        else None,
        arv=Decimal(str(getattr(backend_deal, "arv", 0)))
        if getattr(backend_deal, "arv", None) is not None
        else None,
        repairs=Decimal(str(getattr(backend_deal, "repairs", 0)))
        if getattr(backend_deal, "repairs", None) is not None
        else None,
        offer=Decimal(str(getattr(backend_deal, "offer", 0)))
        if getattr(backend_deal, "offer", None) is not None
        else None,
        mao=Decimal(str(getattr(backend_deal, "mao", 0)))
        if getattr(backend_deal, "mao", None) is not None
        else None,
        notes=notes,
    )


def _estimate_underwriting_summary(
    backend_deal: Deal,
) -> UnderwritingSummary:
    """
    We don't currently persist full UnderwritingResult in DB, so this summary
    reflects what's on the Deal row (ARV, offer, MAO, roi_note).

    Heimdall or the closer can use this plus the raw numbers if needed.
    """
    arv = getattr(backend_deal, "arv", None)
    offer = getattr(backend_deal, "offer", None)
    mao = getattr(backend_deal, "mao", None)
    roi_note = getattr(backend_deal, "roi_note", None)

    # Best-effort LTV/ROI estimates if ARV/offer present.
    ltv = None
    roi = None
    equity_pct = None

    try:
        if arv and offer:
            arv_dec = Decimal(str(arv))
            offer_dec = Decimal(str(offer))
            if arv_dec > 0:
                ltv = offer_dec / arv_dec
        if arv and mao:
            arv_dec = Decimal(str(arv))
            mao_dec = Decimal(str(mao))
            equity = arv_dec - mao_dec
            if arv_dec > 0:
                equity_pct = equity / arv_dec
    except Exception:
        pass

    return UnderwritingSummary(
        recommendation=None,  # closer can infer from roi_note or metrics
        ltv=ltv,
        roi=roi,
        equity_percent_of_arv=equity_pct,
        notes=roi_note,
        raw=None,
    )


def _find_deal_brief(db: Session, backend_deal_id: int) -> Optional[DealBrief]:
    """
    Simple linkage: assume DealBrief.id == backend_deal_id when created by
    our full_deal_pipeline, but fall back gracefully if not found.
    """
    deal_brief = (
        db.query(DealBrief)
        .filter(DealBrief.id == backend_deal_id)
        .first()
    )
    return deal_brief


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

    # 2. Build summaries
    lead_summary = _build_lead_summary(backend_deal)
    deal_brief = _find_deal_brief(db, backend_deal_id)
    deal_summary = _build_deal_summary(backend_deal, deal_brief)
    freeze_summary = _get_latest_freeze_for_deal(db, backend_deal_id)
    uw_summary = _estimate_underwriting_summary(backend_deal)
    buyers = _find_top_buyers(db, deal_brief)

    # 3. Suggested opening script
    if freeze_summary.has_freeze:
        opening = (
            "This deal currently has risk flags from underwriting. "
            "Start by clarifying the seller's expectations and timeline, "
            "then carefully walk through repairs and pricing."
        )
    else:
        opening = (
            "This looks like a viable deal. Start by building rapport, "
            "confirm the seller's motivation and timeline, then move into "
            "numbers with confidence based on your underwriting."
        )

    return ClosingContext(
        lead=lead_summary,
        deal=deal_summary,
        buyers=buyers,
        freeze=freeze_summary,
        underwriting=uw_summary,
        suggested_opening=opening,
    )
