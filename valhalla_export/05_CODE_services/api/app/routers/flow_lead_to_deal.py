# services/api/app/routers/flow_lead_to_deal.py

from __future__ import annotations

from decimal import Decimal
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.geo import infer_province_market
from app.leads import service as lead_service  # Pack 31 service layer
from app.models.match import Buyer, DealBrief
from app.models.deal import Deal  # Backend Deal model
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
from app.services.buyer_liquidity import liquidity_score, record_feedback
from app.services.offer_strategy import compute_offer

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

    # --- Province/Market inference (for Canada-wide routing) ---
    province, market = infer_province_market(payload.deal.region, None)
    corr_id = f"leadflow:{lead_obj.id}"

    emit_kpi(
        db, "WHOLESALE", "lead_created",
        success=True,
        actor="system",
        correlation_id=corr_id,
        detail={"lead_id": lead_obj.id, "province": province, "market": market, "source": payload.lead.source},
    )

    # --- Create Follow-up Ladder automatically (speed-to-lead enforcement) ---
    try:
        create_ladder(
            db=db,
            lead_id=str(lead_obj.id),
            province=province,
            market=market,
            owner="system",
            correlation_id=corr_id,
        )
    except Exception:
        # Non-blocking: if ladder fails, continue flow
        pass

    lead_result = LeadFlowResult(
        id=lead_obj.id,
        name=lead_obj.name,
        email=getattr(lead_obj, "email", None),
        phone=getattr(lead_obj, "phone", None),
        source=getattr(lead_obj, "source", None),
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
    db.commit()
    db.refresh(deal_brief_obj)

    # --- Emit KPI: DealBrief created ---
    emit_kpi(
        db, "WHOLESALE", "deal_brief_created",
        success=True,
        actor="system",
        correlation_id=corr_id,
        detail={"deal_brief_id": deal_brief_obj.id, "lead_id": lead_obj.id},
    )

    # --------- 3. Create backend Deal ---------
    # org_id is required in backend Deal; we use lead.org_id if present.
    org_id = getattr(lead_obj, "org_id", None)
    if org_id is None and payload.lead.org_id is not None:
        org_id = payload.lead.org_id

    if org_id is None:
        # If still None, you may want to enforce this in your model / flow.
        org_id = 0  # fallback; adjust to your multi-tenant strategy

    # --- Auto-compute offer if missing (fail-closed policy enforcement) ---
    offer_val = float(payload.deal.offer) if payload.deal.offer is not None else 0.0
    mao_val = float(payload.deal.mao) if payload.deal.mao is not None else 0.0
    arv_val = float(payload.deal.arv) if payload.deal.arv is not None else 0.0
    repairs_val = float(payload.deal.repairs) if payload.deal.repairs is not None else 0.0

    if (offer_val <= 0.0 or mao_val <= 0.0) and arv_val > 0.0:
        try:
            offer_result = compute_offer(
                db=db,
                province=province or "ON",
                market=market or "ALL",
                arv=arv_val,
                repairs=repairs_val,
                holding_cost=0.0,
            )
            offer_val = offer_result.get("calc", {}).get("recommended_offer", offer_val)
            mao_val = offer_result.get("calc", {}).get("mao", mao_val)
        except Exception:
            # Non-blocking: if offer computation fails, continue with defaults (fail-closed)
            pass

    backend_deal = Deal(
        org_id=org_id,
        legacy_id=None,
        status="draft",
        city=None,
        state=None,
        price=float(payload.deal.price) if payload.deal.price is not None else None,
        lead_id=lead_obj.id,
        arv=arv_val,
        repairs=repairs_val,
        offer=offer_val,
        mao=mao_val,
        roi_note=payload.deal.roi_note or "",
    )

    db.add(backend_deal)
    db.commit()
    db.refresh(backend_deal)

    # --- Emit KPI: backend Deal created ---
    emit_kpi(
        db, "WHOLESALE", "backend_deal_created",
        success=True,
        actor="system",
        correlation_id=corr_id,
        detail={"deal_id": backend_deal.id, "offer": offer_val, "mao": mao_val},
    )

    deal_result = DealFlowResult(
        id=deal_brief_obj.id,  # Match system id; backend_deal.id is also available if needed
        headline=deal_brief_obj.headline,
        region=deal_brief_obj.region,
        property_type=deal_brief_obj.property_type,
        price=deal_brief_obj.price,
        status=deal_brief_obj.status,
    )

    # --------- 4. Buyer matching (real, not stubbed) ---------
    # --- Fetch liquidity score before matching ---
    liq_score = None
    if province:
        try:
            liq_score = liquidity_score(
                db=db,
                province=province,
                market=market or "ALL",
                property_type=deal_brief_obj.property_type,
            )
        except Exception:
            # Non-blocking: if liquidity fetch fails, proceed
            pass

    # --- Emit KPI: Match attempt ---
    emit_kpi(
        db, "BUYER_MATCH", "match_attempt",
        success=True,
        actor="system",
        correlation_id=corr_id,
        detail={"deal_brief_id": deal_brief_obj.id, "liquidity_score": liq_score},
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

    # --- Record buyer feedback if match found (liquidity signal) ---
    if province and matched_candidates:
        try:
            record_feedback(
                db=db,
                province=province,
                market=market or "ALL",
                property_type=deal_brief_obj.property_type,
                signal_type="RESPONDED",
                buyer_id=str(matched_candidates[0].buyer_id),
                correlation_id=corr_id,
                note="auto_signal_from_match_flow",
            )
        except Exception:
            # Non-blocking: if feedback recording fails, continue
            pass

    # --- Emit KPI: Match result ---
    emit_kpi(
        db, "BUYER_MATCH", "match_result",
        success=True,
        actor="system",
        correlation_id=corr_id,
        detail={"matched_count": len(matched_candidates), "liquidity_score": liq_score},
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
        "liquidity_score": liq_score,
    }

    return LeadToDealResponse(
        lead=lead_result,
        deal=deal_result,
        matched_buyers=matched_candidates,
        notes=" ".join(notes_parts) if notes_parts else None,
        metadata=metadata,
    )
