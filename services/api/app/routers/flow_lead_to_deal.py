# services/api/app/routers/flow_lead_to_deal.py

from __future__ import annotations

from decimal import Decimal
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.leads import service as lead_service  # Pack 31 service layer
from app.models.match import Buyer, DealBrief
from app.schemas.flows_lead_to_deal import (
    BuyerMatchCandidate,
    LeadFlowResult,
    LeadToDealRequest,
    LeadToDealResponse,
    DealFlowResult,
)
from app.schemas.leads import LeadCreate  # Pack 31 create schema
from app.schemas.match import DealBriefIn  # Match system deal brief schema

router = APIRouter(
    prefix="/flow",
    tags=["Flow", "LeadToDeal"],
)


# ---------- Internal helpers ----------


def _safe_decimal(value: object | None) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except Exception:
        return None


def _normalize_price_range(
    min_price: Decimal | None,
    max_price: Decimal | None,
) -> tuple[Decimal | None, Decimal | None]:
    if min_price is not None and max_price is not None and max_price < min_price:
        return max_price, min_price
    return min_price, max_price


def _split_csv(value: str | None) -> List[str]:
    if not value:
        return []
    return [part.strip().lower() for part in value.split(",") if part.strip()]


def _score_buyer_for_deal(
    buyer: Buyer,
    deal: DealBrief,
) -> BuyerMatchCandidate | None:
    """
    Very simple first-pass matcher based on:

    - region overlap
    - property_type overlap
    - price range inclusion
    - beds/baths minimums

    Returns a BuyerMatchCandidate with score 0–1 or None if no signal.
    """
    reasons: List[str] = []
    score_components: List[float] = []

    # Regions / markets
    buyer_regions = _split_csv(buyer.regions)
    deal_region = (deal.region or "").strip().lower()
    if buyer_regions and deal_region:
        if deal_region in buyer_regions:
            score_components.append(0.25)
            reasons.append("region_match")

    # Property types
    buyer_types = _split_csv(buyer.property_types)
    deal_type = (deal.property_type or "").strip().lower()
    if buyer_types and deal_type:
        if deal_type in buyer_types:
            score_components.append(0.25)
            reasons.append("property_type_match")

    # Price range
    deal_price = _safe_decimal(deal.price)
    min_price = _safe_decimal(getattr(buyer, "min_price", None))
    max_price = _safe_decimal(getattr(buyer, "max_price", None))
    min_price, max_price = _normalize_price_range(min_price, max_price)

    if deal_price is not None and (min_price is not None or max_price is not None):
        in_range = True
        if min_price is not None and deal_price < min_price:
            in_range = False
        if max_price is not None and deal_price > max_price:
            in_range = False

        if in_range:
            score_components.append(0.3)
            reasons.append("price_match")

    # Beds / baths
    if deal.beds is not None:
        min_beds = getattr(buyer, "min_beds", None)
        if min_beds is not None and deal.beds >= min_beds:
            score_components.append(0.1)
            reasons.append("beds_ok")

    if deal.baths is not None:
        min_baths = getattr(buyer, "min_baths", None)
        if min_baths is not None and deal.baths >= min_baths:
            score_components.append(0.1)
            reasons.append("baths_ok")

    if not score_components:
        return None

    score = sum(score_components)
    if score > 1.0:
        score = 1.0

    return BuyerMatchCandidate(
        buyer_id=buyer.id,
        name=buyer.name,
        email=getattr(buyer, "email", None),
        phone=getattr(buyer, "phone", None),
        score=score,
        reasons=reasons,
    )


# ---------- Main flow endpoint ----------


@router.post(
    "/lead_to_deal",
    response_model=LeadToDealResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create lead, create deal brief, and match buyers",
    description=(
        "End-to-end flow:\n"
        "- Create a lead (Pack 31 lead system)\n"
        "- Create a DealBrief in the match system\n"
        "- Optionally match buyers using a simple buy-box matcher\n"
    ),
)
def create_lead_and_deal_flow(
    payload: LeadToDealRequest,
    db: Session = Depends(get_db),
) -> LeadToDealResponse:
    # --------- 1. Create Lead (Pack 31) ---------
    lead_in = LeadCreate(
        name=payload.lead.name,
        email=payload.lead.email,
        phone=payload.lead.phone,
        source=payload.lead.source,
        status="new",  # default for new flow
    )
    lead_obj = lead_service.create_lead(db, lead_in)

    if not lead_obj:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create lead.",
        )

    lead_result = LeadFlowResult(
        id=lead_obj.id,
        name=lead_obj.name,
        email=getattr(lead_obj, "email", None),
        phone=getattr(lead_obj, "phone", None),
        source=getattr(lead_obj, "source", None),
    )

    # --------- 2. Create DealBrief (match system) ---------
    deal_in = DealBriefIn(
        headline=payload.deal.headline,
        region=payload.deal.region,
        property_type=payload.deal.property_type,
        price=payload.deal.price,
        beds=payload.deal.beds,
        baths=payload.deal.baths,
        notes=payload.deal.notes,
        status=payload.deal.status or "active",
    )
    deal_obj = DealBrief(**deal_in.model_dump())

    db.add(deal_obj)
    db.commit()
    db.refresh(deal_obj)

    deal_result = DealFlowResult(
        id=deal_obj.id,
        headline=deal_obj.headline,
        region=deal_obj.region,
        property_type=deal_obj.property_type,
        price=deal_obj.price,
        status=deal_obj.status,
    )

    # --------- 3. Buyer matching (real, not stubbed) ---------
    matched_candidates: List[BuyerMatchCandidate] = []
    if payload.match_settings.match_buyers:
        buyers_query = db.query(Buyer).filter(Buyer.active.is_(True))
        buyers = buyers_query.all()

        for buyer in buyers:
            candidate = _score_buyer_for_deal(buyer, deal_obj)
            if candidate is None:
                continue
            if candidate.score < payload.match_settings.min_match_score:
                continue
            matched_candidates.append(candidate)

        # Sort by score descending and trim to max_results
        matched_candidates.sort(key=lambda c: c.score, reverse=True)
        matched_candidates = matched_candidates[: payload.match_settings.max_results]

    notes_parts: List[str] = []
    if matched_candidates:
        notes_parts.append(
            f"{len(matched_candidates)} buyers matched "
            f"(min_score={payload.match_settings.min_match_score})."
        )
    else:
        if payload.match_settings.match_buyers:
            notes_parts.append(
                "No buyers matched the criteria for this deal at the current threshold."
            )
        else:
            notes_parts.append("Buyer matching was disabled for this flow.")

    metadata = {
        "min_match_score": payload.match_settings.min_match_score,
        "max_results": payload.match_settings.max_results,
    }

    return LeadToDealResponse(
        lead=lead_result,
        deal=deal_result,
        matched_buyers=matched_candidates,
        notes=" ".join(notes_parts) if notes_parts else None,
        metadata=metadata,
    )
