# services/api/app/routers/flow_lead_to_deal.py

from __future__ import annotations

from decimal import Decimal
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.dependencies import require_prime_control_key
from app.core.geo import infer_province_market
from app.leads import service as lead_service  # Pack 31 service layer
from app.models.match import Buyer, DealBrief
from app.models.deal import Deal, DealBriefLink
from app.services.buyer_liquidity import liquidity_score
from app.schemas.flows_lead_to_deal import (
    BuyerMatchCandidate,
    DealFlowResult,
    LeadFlowResult,
    LeadToDealRequest,
    LeadToDealResponse,
)
from app.leads.schemas import LeadCreate  # Pack 31 create schema
from app.schemas.match import DealBriefIn  # Match system deal brief schema
from app.services.kpi import emit_kpi
from app.services.followup_ladder import create_ladder
from app.services.offer_strategy import compute_offer

router = APIRouter(
    prefix="/flow",
    tags=["Flow", "LeadToDeal"],
    dependencies=[Depends(require_prime_control_key)],
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
    buyer_regions = _split_csv(getattr(buyer, "regions", None))
    deal_region = (deal.region or "").strip().lower()
    if buyer_regions and deal_region:
        if deal_region in buyer_regions:
            score_components.append(0.25)
            reasons.append("region_match")

    # Property types
    buyer_types = _split_csv(getattr(buyer, "property_types", None))
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
    summary="Create lead, create deal (brief + backend), and match buyers",
    description=(
        "End-to-end flow:\n"
        "- Create a lead (Pack 31 lead system)\n"
        "- Create a DealBrief in the match system\n"
        "- Create a backend Deal linked to the lead\n"
        "- Optionally match buyers using a simple buy-box matcher\n"
    ),
)
def create_lead_and_deal_flow(
    payload: LeadToDealRequest,
    db: Session = Depends(get_db),
) -> LeadToDealResponse:
    try:
        lead_in = LeadCreate(
            lead_name=payload.lead.name, lead_email=payload.lead.email,
            lead_phone=payload.lead.phone, source=payload.lead.source or "pipeline",
            property_address=payload.lead.address,
        )
        lead_obj = lead_service.create_lead(db, lead_in, commit=False)
    except ValueError:
        raise HTTPException(status_code=422, detail="Valid lead name, email and phone are required") from None

    province, market = infer_province_market(payload.deal.region, None)
    corr_id = f"leadflow:{lead_obj.id}"
    emit_kpi(
        db, "WHOLESALE", "lead_created", success=True, actor="system",
        correlation_id=corr_id, detail={"lead_id": lead_obj.id, "province": province, "market": market},
        commit=False,
    )
    create_ladder(db, str(lead_obj.id), province, market, "system", corr_id, commit=False)
    lead_result = LeadFlowResult(
        id=lead_obj.id, name=lead_obj.lead_name, email=lead_obj.lead_email,
        phone=lead_obj.lead_phone, source=lead_obj.source,
    )

    # --------- 2. Create DealBrief (match system) ---------
    deal_brief_in = DealBriefIn(
        headline=payload.deal.headline,
        region=payload.deal.region,
        property_type=payload.deal.property_type,
        price=payload.deal.price,
        beds=payload.deal.beds,
        baths=payload.deal.baths,
        notes=payload.deal.notes,
        status=payload.deal.status or "active",
    )
    deal_brief_obj = DealBrief(**deal_brief_in.model_dump())

    db.add(deal_brief_obj)
    db.flush()

    # --- Emit KPI: DealBrief created ---
    emit_kpi(
        db, "WHOLESALE", "deal_brief_created",
        success=True,
        actor="system",
        correlation_id=corr_id,
        detail={"deal_brief_id": deal_brief_obj.id, "lead_id": lead_obj.id},
        commit=False,
    )

    mao = payload.deal.mao
    offer_evidence_id = None
    if mao is None and province and payload.deal.arv and payload.deal.repairs is not None:
        try:
            with db.begin_nested():
                calculation = compute_offer(
                    db, province, market or "ALL", float(payload.deal.arv),
                    float(payload.deal.repairs), None, None, corr_id, commit=False,
                )
                mao = calculation["calc"]["mao"]
                offer_evidence_id = calculation["evidence_id"]
        except (RuntimeError, SQLAlchemyError):
            # Unavailable policy leaves the draft without a calculated offer.
            pass
    backend_deal = Deal(
        lead_id=lead_obj.id, title=deal_brief_obj.headline, stage="draft", status="active",
        arv=payload.deal.arv, estimated_repair_cost=payload.deal.repairs, max_allowable_offer=mao,
        notes=payload.deal.roi_note,
    )
    db.add(backend_deal)
    db.flush()
    db.add(DealBriefLink(deal_id=backend_deal.id, brief_id=deal_brief_obj.id))
    emit_kpi(
        db, "WHOLESALE", "backend_deal_created", success=True, actor="system",
        correlation_id=corr_id, detail={"deal_id": backend_deal.id, "offer_evidence_id": offer_evidence_id},
        commit=False,
    )

    deal_result = DealFlowResult(
        id=deal_brief_obj.id,  # Match system id; backend_deal.id is also available if needed
        headline=deal_brief_obj.headline,
        region=deal_brief_obj.region,
        property_type=deal_brief_obj.property_type,
        price=deal_brief_obj.price,
        status=deal_brief_obj.status,
    )

    liquidity = None
    if province and payload.match_settings.match_buyers:
        liquidity = liquidity_score(db, province, market or "ALL", deal_brief_obj.property_type, create=False)

    if payload.match_settings.match_buyers:
        emit_kpi(
            db, "BUYER_MATCH", "match_attempt", success=True, actor="system",
            correlation_id=corr_id, detail={"deal_brief_id": deal_brief_obj.id}, commit=False,
        )

    matched_candidates: List[BuyerMatchCandidate] = []
    if payload.match_settings.match_buyers:
        buyers_query = db.query(Buyer).filter(Buyer.active.is_(True))
        buyers = buyers_query.all()

        for buyer in buyers:
            candidate = _score_buyer_for_deal(buyer, deal_brief_obj)
            if candidate is None:
                continue
            if candidate.score < payload.match_settings.min_match_score:
                continue
            matched_candidates.append(candidate)

        # Sort by score descending and trim to max_results
        matched_candidates.sort(key=lambda c: c.score, reverse=True)
        matched_candidates = matched_candidates[: payload.match_settings.max_results]

    if payload.match_settings.match_buyers:
        emit_kpi(
            db, "BUYER_MATCH", "match_result", success=True, actor="system",
            correlation_id=corr_id, detail={"matched_count": len(matched_candidates)}, commit=False,
        )

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
        "lead_id": lead_obj.id,
        "deal_brief_id": deal_brief_obj.id,
        "backend_deal_id": backend_deal.id,
        "min_match_score": payload.match_settings.min_match_score,
        "max_results": payload.match_settings.max_results,
        "province": province,
        "market": market,
        "liquidity_score": liquidity,
        "offer_evidence_id": offer_evidence_id,
    }

    response = LeadToDealResponse(
        lead=lead_result,
        deal=deal_result,
        matched_buyers=matched_candidates,
        notes=" ".join(notes_parts) if notes_parts else None,
        metadata=metadata,
    )
    db.commit()
    return response
