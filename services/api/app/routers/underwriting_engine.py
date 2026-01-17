# services/api/app/routers/underwriting_engine.py

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.deal import Deal  # backend Deal model
from app.schemas.underwriting_engine import (
    UnderwriteDealRequest,
    UnderwriteDealResponse,
)
from app.services.freeze_events import log_freeze_event
from app.services.underwriting_engine import run_underwriting

router = APIRouter(
    prefix="/flow",
    tags=["Flow", "Underwriting"],
)


@router.post(
    "/underwrite_deal",
    response_model=UnderwriteDealResponse,
    status_code=status.HTTP_200_OK,
    summary="Run underwriting on a deal and apply policy rules.",
    description=(
        "Calculates metrics (LTV, ROI, equity, holding costs) and applies "
        "policy thresholds to produce a recommendation. Optionally updates "
        "the backend Deal row and logs a freeze_event if policies are breached."
    ),
)
def underwrite_deal(
    payload: UnderwriteDealRequest,
    db: Session = Depends(get_db),
) -> UnderwriteDealResponse:
    # 1. Run core underwriting logic
    result = run_underwriting(payload)

    deal_id = payload.deal.deal_id
    org_id = payload.deal.org_id

    # 2. Optionally update backend Deal with summary numbers
    if deal_id is not None:
        deal_obj = db.query(Deal).filter(Deal.id == deal_id).first()
        if deal_obj is not None:
            # Only overwrite if values look sane
            deal_obj.arv = float(payload.deal.arv)
            deal_obj.repairs = float(payload.deal.repairs)
            deal_obj.offer = float(payload.deal.purchase_price)
            deal_obj.mao = float(result.metrics.total_project_cost)
            deal_obj.roi_note = (
                result.flags.notes
                or f"Recommendation: {result.recommendation}"
            )
            db.add(deal_obj)
            db.commit()
            db.refresh(deal_obj)

    # 3. Log freeze_event if we breached policy
    freeze_created = False
    flags = result.flags

    if flags.breach_ltv or flags.breach_roi or flags.breach_equity:
        reason_parts = []
        if flags.breach_ltv:
            reason_parts.append("LTV above policy.")
        if flags.breach_roi:
            reason_parts.append("ROI below policy.")
        if flags.breach_equity:
            reason_parts.append("Equity below policy.")

        reason = " ".join(reason_parts)
        severity = "critical" if flags.breach_ltv and flags.breach_roi else "warn"

        log_freeze_event(
            db,
            source="underwriting_engine",
            event_type="underwriting_policy_violation",
            severity=severity,
            reason=reason,
            payload={
                "deal_id": deal_id,
                "org_id": org_id,
                "metrics": {
                    "ltv": str(result.metrics.ltv),
                    "roi": str(result.metrics.roi),
                    "equity_percent_of_arv": str(
                        result.metrics.equity_percent_of_arv
                    ),
                },
                "policy": {
                    "max_ltv": str(result.policy.max_ltv),
                    "min_roi": str(result.policy.min_roi),
                    "min_equity_percent": str(
                        result.policy.min_equity_percent
                    ),
                },
            },
            notes="Auto-created by underwriting_engine.",
        )
        freeze_created = True

    return UnderwriteDealResponse(
        deal_id=deal_id,
        org_id=org_id,
        result=result,
        freeze_event_created=freeze_created,
    )
