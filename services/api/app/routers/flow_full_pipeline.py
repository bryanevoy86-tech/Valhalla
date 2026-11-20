# services/api/app/routers/flow_full_pipeline.py

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.dependencies import require_prime_control_key
from app.leads import service as lead_service  # Pack 31 lead service
from app.models.match import Buyer, DealBrief
from app.models.deal import Deal, DealBriefLink
from app.models.freeze_events import FreezeEvent
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
from app.services.underwriting_engine import run_underwriting
from app.routers.flow_lead_to_deal import _score_buyer_for_deal  # reuse matcher


router = APIRouter(
    prefix="/flow",
    tags=["Flow", "FullPipeline"],
)


@router.post(
    "/full_deal_pipeline",
    dependencies=[Depends(require_prime_control_key)],
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
    result = build_full_deal_pipeline(payload, db)
    db.commit()
    return result


def build_full_deal_pipeline(payload: FullDealPipelineRequest, db: Session) -> FullDealPipelineResponse:
    """Stage internal pipeline records in the caller's transaction."""
    # --------- 1. Create Lead (Pack 31) ---------
    try:
        lead_in = LeadCreate(
            lead_name=payload.lead.name,
            lead_email=payload.lead.email,
            lead_phone=payload.lead.phone,
            source=payload.lead.source or "pipeline",
            property_address=payload.lead.address,
        )
        lead_obj = lead_service.create_lead(db, lead_in, commit=False)
    except (ValueError, ValidationError):
        raise HTTPException(status_code=422, detail="Valid lead name, email and phone are required") from None

    lead_result = LeadFlowResult(
        id=lead_obj.id,
        name=lead_obj.lead_name,
        email=lead_obj.lead_email,
        phone=lead_obj.lead_phone,
        source=lead_obj.source,
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
    db.flush()

    deal_result = DealFlowResult(
        id=deal_brief_obj.id,
        headline=deal_brief_obj.headline,
        region=deal_brief_obj.region,
        property_type=deal_brief_obj.property_type,
        price=deal_brief_obj.price,
        status=deal_brief_obj.status,
    )

    # --------- 3. Create backend Deal ---------
    backend_deal = Deal(
        lead_id=lead_obj.id,
        title=deal_brief_obj.headline,
        stage="draft",
        status="active",
        arv=payload.underwriting.arv,
        estimated_repair_cost=payload.underwriting.repairs,
        max_allowable_offer=payload.deal.mao,
        notes=payload.deal.roi_note,
    )
    db.add(backend_deal)
    db.flush()
    db.add(DealBriefLink(deal_id=backend_deal.id, brief_id=deal_brief_obj.id))

    # --------- 4. Run underwriting ---------
    uw = payload.underwriting
    uw_deal_input = UnderwritingDealInput(
        deal_id=backend_deal.id,
        org_id=payload.lead.org_id or 0,
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

        db.add(FreezeEvent(
            deal_id=str(backend_deal.id),
            event_type="underwriting_policy_violation",
            event_name="full_deal_pipeline",
            notes=reason,
        ))
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
