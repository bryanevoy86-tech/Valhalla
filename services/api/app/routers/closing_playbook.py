# services/api/app/routers/closing_playbook.py

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.deal import Deal
from app.models.match import DealBrief, Buyer
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
    tags=["Flow", "ClosingPlaybook"],
)


def _get_latest_freeze_for_deal(
    db: Session,
    backend_deal_id: int,
) -> FreezeSummary:
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


def _build_lead_summary_from_deal(deal: Deal) -> LeadSummary:
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


def _find_deal_brief(db: Session, backend_deal_id: int) -> DealBrief | None:
    return (
        db.query(DealBrief)
        .filter(DealBrief.id == backend_deal_id)
        .first()
    )


def _build_deal_summary(
    backend_deal: Deal,
    deal_brief: DealBrief | None,
) -> DealSummary:
    from decimal import Decimal

    headline = getattr(deal_brief, "headline", None) if deal_brief else None
    region = getattr(deal_brief, "region", None) if deal_brief else None
    property_type = getattr(deal_brief, "property_type", None) if deal_brief else None
    notes = getattr(deal_brief, "notes", None) if deal_brief else None

    price = getattr(backend_deal, "price", None)
    arv = getattr(backend_deal, "arv", None)
    repairs = getattr(backend_deal, "repairs", None)
    offer = getattr(backend_deal, "offer", None)
    mao = getattr(backend_deal, "mao", None)

    def _d(val: Any | None) -> Decimal | None:
        if val is None:
            return None
        try:
            return Decimal(str(val))
        except Exception:
            return None

    return DealSummary(
        backend_deal_id=backend_deal.id,
        deal_brief_id=deal_brief.id if deal_brief else None,
        status=backend_deal.status,
        headline=headline,
        region=region,
        property_type=property_type,
        price=_d(price),
        arv=_d(arv),
        repairs=_d(repairs),
        offer=_d(offer),
        mao=_d(mao),
        notes=notes,
    )


def _estimate_underwriting_summary(
    backend_deal: Deal,
) -> UnderwritingSummary:
    from decimal import Decimal

    arv = getattr(backend_deal, "arv", None)
    offer = getattr(backend_deal, "offer", None)
    mao = getattr(backend_deal, "mao", None)
    roi_note = getattr(backend_deal, "roi_note", None)

    ltv = None
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
        recommendation=None,
        ltv=ltv,
        roi=None,
        equity_percent_of_arv=equity_pct,
        notes=roi_note,
        raw=None,
    )


def _find_top_buyers(
    db: Session,
    deal_brief: DealBrief | None,
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


def _build_script(context: ClosingContext) -> Dict[str, Any]:
    """
    Build a structured playbook the closer (or Heimdall) can follow.
    """
    lead = context.lead
    deal = context.deal
    freeze = context.freeze
    uw = context.underwriting

    price_str = f"${deal.price:,}" if deal.price is not None else "the price"
    arv_str = f"${deal.arv:,}" if deal.arv is not None else "the after-repair value"
    region = deal.region or "your area"

    script: Dict[str, Any] = {}

    # Opening
    script["opening"] = context.suggested_opening

    # Rapport phase
    script["rapport_questions"] = [
        f"Hey {lead.name}, how have things been at the property on {lead.address or 'the place'}?",
        "What's got you thinking about making a move right now?",
        "If everything went perfectly for you with this sale, what would that look like?",
    ]

    # Discovery / pain
    script["diagnostic_questions"] = [
        "What's the biggest headache with the property for you right now?",
        "Have you already had other offers or conversations with agents/investors?",
        "How quickly do you ideally need this to be wrapped up?",
    ]

    # Numbers framing
    framing_lines: List[str] = []
    if uw.ltv is not None:
        framing_lines.append(
            f"Right now, at the numbers we're looking at, we're around {uw.ltv:.1%} "
            f"of what we think the property is worth after repairs."
        )
    if uw.equity_percent_of_arv is not None:
        framing_lines.append(
            f"That leaves roughly {uw.equity_percent_of_arv:.1%} of the value as "
            f"room for repairs, risk, and profit so the deal still makes sense."
        )
    if not framing_lines:
        framing_lines.append(
            "I want to walk through the numbers with you so we both see the same story "
            "on price, repairs, and what makes the deal work."
        )

    script["numbers_framing"] = framing_lines

    # Offer framing
    script["offer_framing"] = [
        f"If we can make {price_str} work, with us handling the repairs and hassle, "
        f"is that something that would put you in a good spot?",
        "On a scale of 1–10, where 10 means you're ready to sign today, where are you right now?",
    ]

    # Objection handling
    script["objection_prompts"] = [
        "What would need to change in this offer to make it a no-brainer for you?",
        "Sounds like the number is the main thing holding you back — is that fair?",
        "If we could tighten up the timeline or terms instead of the price, would that help?",
    ]

    # Closing prompts
    if freeze.has_freeze:
        script["closing_prompts"] = [
            "Given there are some risk flags on our side with the numbers, "
            "I want to be transparent and make sure this still feels fair to you.",
            "If we could agree on this today, are you comfortable moving forward so we "
            "can start the paperwork?",
        ]
    else:
        script["closing_prompts"] = [
            "If this all sounds good, are you comfortable moving forward today so we can lock this in?",
            "Would you like to move ahead with this and let us take the stress of the property off your plate?",
        ]

    # Summary line for Heimdall
    script["summary_for_ai"] = (
        f"Closing context for a {deal.property_type or 'property'} in {region} with "
        f"headline '{deal.headline or ''}'. Lead {lead.name} appears motivated due to "
        f"{lead.tags or 'general reasons'}. Use the script sections to guide the call, "
        "but adapt based on real-time responses."
    )

    return script


@router.get(
    "/closing_playbook/{backend_deal_id}",
    status_code=status.HTTP_200_OK,
    summary="Generate a closing playbook for a deal",
    description=(
        "Builds a closing playbook (script sections) for a given backend Deal. "
        "This is what Heimdall or the closer engine can follow in a live call."
    ),
)
def get_closing_playbook(
    backend_deal_id: int,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    # 1. Load backend deal
    deal = db.query(Deal).filter(Deal.id == backend_deal_id).first()
    if deal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deal with id {backend_deal_id} not found.",
        )

    # 2. Build pieces of the context (basically replicate closing_context but inline)
    lead_summary = _build_lead_summary_from_deal(deal)
    deal_brief = _find_deal_brief(db, backend_deal_id)
    deal_summary = _build_deal_summary(deal, deal_brief)
    freeze_summary = _get_latest_freeze_for_deal(db, backend_deal_id)
    uw_summary = _estimate_underwriting_summary(deal)
    buyers = _find_top_buyers(db, deal_brief)

    # 3. Suggested opening (reused logic)
    if freeze_summary.has_freeze:
        suggested_opening = (
            "This deal currently has risk flags from underwriting. Start by "
            "clarifying the seller's expectations and timeline, then carefully "
            "walk through repairs and pricing."
        )
    else:
        suggested_opening = (
            "This looks like a viable deal. Start by building rapport, confirm "
            "the seller's motivation and timeline, then move into numbers with "
            "confidence based on your underwriting."
        )

    context = ClosingContext(
        lead=lead_summary,
        deal=deal_summary,
        buyers=buyers,
        freeze=freeze_summary,
        underwriting=uw_summary,
        suggested_opening=suggested_opening,
    )

    script = _build_script(context)

    return {
        "context": context,
        "script": script,
    }
