# services/api/app/routers/flow_full_pipeline.py

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.leads import service as lead_service  # Pack 31 lead service
from app.models.match import Buyer, DealBrief
from app.models.deal import Deal  # Backend Deal model
from app.schemas.flows_lead_to_deal import (
    LeadFlowResult,
    DealFlowResult,
    BuyerMatchCandidate,
)
from app.schemas.flow_full_pipeline import (
    FullDealPipelineRequest,
    FullDealPipelineResponse,
)
from app.leads.schemas import LeadCreate
from app.schemas.match import DealBriefIn
from app.schemas.underwriting_engine import (
    UnderwriteDealRequest,
    UnderwritingDealInput,
)
from app.services.freeze_events import log_freeze_event
from app.services.underwriting_engine import run_underwriting
from app.routers.flow_lead_to_deal import _score_buyer_for_deal  # reuse matcher


router = APIRouter(
    prefix="/flow",
    tags=["Flow", "FullPipeline"],
)


@router.post(
    "/full_deal_pipeline",
    response_model=FullDealPipelineResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Full deal pipeline: lead + deal + underwriting + buyer match",
    description=(
        "One-shot pipeline that:\n"
        "- creates a lead (Pack 31)\n"
        "- creates a DealBrief (match system)\n"
        "- creates a backend Deal tied to the lead\n"
        "- runs underwriting with policy rules\n"
        "- matches buyers off their buy-box\n"
        "- logs a freeze_event if underwriting breaches policy\n"
    ),
)
def run_full_deal_pipeline(
    payload: FullDealPipelineRequest,
    db: Session = Depends(get_db),
) -> FullDealPipelineResponse:
    # --------- 1. Create Lead (Pack 31) ---------
    lead_in = LeadCreate(
        name=payload.lead.name,
        email=payload.lead.email,
        phone=payload.lead.phone,
        source=payload.lead.source,
        status="new",
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
    deal_brief_obj = DealBrief(**deal_in.model_dump())
    db.add(deal_brief_obj)
    db.commit()
    db.refresh(deal_brief_obj)

    deal_result = DealFlowResult(
        id=deal_brief_obj.id,
        headline=deal_brief_obj.headline,
        region=deal_brief_obj.region,
        property_type=deal_brief_obj.property_type,
        price=deal_brief_obj.price,
        status=deal_brief_obj.status,
    )

    # --------- 3. Create backend Deal ---------
    org_id = getattr(lead_obj, "org_id", None)
    if org_id is None:
        org_id = payload.lead.org_id

    if org_id is None:
        org_id = 0  # fallback; adjust to your multi-tenant strategy

    backend_deal = Deal(
        org_id=org_id,
        legacy_id=None,
        status="draft",
        city=None,
        state=None,
        price=float(payload.deal.price) if payload.deal.price is not None else None,
        lead_id=lead_obj.id,
        arv=float(payload.deal.arv) if payload.deal.arv is not None else 0.0,
        repairs=float(payload.deal.repairs) if payload.deal.repairs is not None else 0.0,
        offer=float(payload.underwriting.purchase_price),
        mao=float(payload.deal.mao) if payload.deal.mao is not None else 0.0,
        roi_note=payload.deal.roi_note or "",
    )
    db.add(backend_deal)
    db.commit()
    db.refresh(backend_deal)

    # --------- 4. Run underwriting ---------
    uw = payload.underwriting
    uw_deal_input = UnderwritingDealInput(
        deal_id=backend_deal.id,
        org_id=org_id,
        arv=uw.arv,
        purchase_price=uw.purchase_price,
        repairs=uw.repairs,
        closing_costs=uw.closing_costs,
        holding_months=uw.holding_months,
        monthly_taxes=uw.monthly_taxes,
        monthly_insurance=uw.monthly_insurance,
        monthly_utilities=uw.monthly_utilities,
        monthly_hoa=uw.monthly_hoa,
        monthly_other=uw.monthly_other,
        expected_rent=uw.expected_rent,
    )
    uw_request = UnderwriteDealRequest(
        deal=uw_deal_input,
        policy=uw.policy,
    )
    underwriting_result = run_underwriting(uw_request)

    # Update backend deal summary fields based on underwriting
    backend_deal.arv = float(uw.arv)
    backend_deal.repairs = float(uw.repairs)
    backend_deal.offer = float(uw.purchase_price)
    backend_deal.mao = float(underwriting_result.metrics.total_project_cost)
    backend_deal.roi_note = (
        underwriting_result.flags.notes
        or f"Recommendation: {underwriting_result.recommendation}"
    )
    db.add(backend_deal)
    db.commit()
    db.refresh(backend_deal)

    # --------- 5. Log freeze_event if policy breached ---------
    freeze_created = False
    flags = underwriting_result.flags
    if flags.breach_ltv or flags.breach_roi or flags.breach_equity:
        reason_parts = []
        if flags.breach_ltv:
            reason_parts.append("LTV above policy.")
        if flags.breach_roi:
            reason_parts.append("ROI below policy.")
        if flags.breach_equity:
            reason_parts.append("Equity below policy.")
        reason = " ".join(reason_parts) or "Underwriting policy violation."

        severity = "critical" if flags.breach_ltv and flags.breach_roi else "warn"

        log_freeze_event(
            db,
            source="full_deal_pipeline",
            event_type="underwriting_policy_violation",
            severity=severity,
            reason=reason,
            payload={
                "backend_deal_id": backend_deal.id,
                "deal_brief_id": deal_brief_obj.id,
                "lead_id": lead_obj.id,
                "metrics": {
                    "ltv": str(underwriting_result.metrics.ltv),
                    "roi": str(underwriting_result.metrics.roi),
                    "equity_percent_of_arv": str(
                        underwriting_result.metrics.equity_percent_of_arv
                    ),
                },
            },
            notes="Auto-created by full_deal_pipeline.",
        )
        freeze_created = True

    # --------- 6. Buyer matching ---------
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

        matched_candidates.sort(key=lambda c: c.score, reverse=True)
        matched_candidates = matched_candidates[: payload.match_settings.max_results]

    # --------- 7. Notes / metadata ---------
    notes_parts: List[str] = []
    notes_parts.append(
        f"Underwriting recommendation: {underwriting_result.recommendation}."
    )

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

    if freeze_created:
        notes_parts.append(
            "Freeze event logged due to underwriting policy breach."
        )

    metadata = {
        "lead_id": str(lead_obj.id),
        "deal_brief_id": str(deal_brief_obj.id),
        "backend_deal_id": str(backend_deal.id),
        "min_match_score": str(payload.match_settings.min_match_score),
        "max_results": str(payload.match_settings.max_results),
        "recommendation": underwriting_result.recommendation,
    }

    return FullDealPipelineResponse(
        lead=lead_result,
        deal=deal_result,
        backend_deal_id=backend_deal.id,
        underwriting_result=underwriting_result,
        matched_buyers=matched_candidates,
        freeze_event_created=freeze_created,
        notes=" ".join(notes_parts) if notes_parts else None,
        metadata=metadata,
    )
