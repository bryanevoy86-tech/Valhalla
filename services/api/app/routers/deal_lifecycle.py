"""Private deal workflow over the canonical reads and planning commands."""

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.dependencies import require_prime_control_key
from app.models.audit_log import AuditLog
from app.models.deal import Deal
from app.routers.closing_playbook import get_closing_playbook
from app.routers.flow_notifications import prepare_deal_notifications
from app.routers.flow_prepare_closing import _find_top_buyers, get_closing_context
from app.routers.flow_profit_allocation import calculate_profit_allocation
from app.routers.underwriting_engine import apply_underwriting
from app.schemas.deal_lifecycle import (
    DealLifecycleSummary,
    LifecycleStep,
    RunLifecycleActionRequest,
    RunLifecycleActionResponse,
)
from app.schemas.notifications_flow import NotifyDealPartiesRequest
from app.schemas.profit_allocation import RunProfitAllocationRequest
from app.schemas.underwriting_engine import UnderwriteDealRequest
from app.services.deal_context import linked_brief

router = APIRouter(
    prefix="/lifecycle", tags=["Lifecycle"],
    dependencies=[Depends(require_prime_control_key)],
)

LIFECYCLE_STAGES = (
    "lead_created", "deal_brief_created", "backend_deal_created",
    "underwriting_complete", "buyer_matching_complete", "closing_context_ready",
    "closing_call_started", "closing_call_completed", "profit_realized",
)
ACTION_STAGE = {
    "run_underwriting": "underwriting_complete",
    "match_buyers": "buyer_matching_complete",
    "prepare_closing": "closing_context_ready",
    "generate_playbook": "closing_context_ready",
    "notify_parties": None,
    "profit_allocation": None,
}


def _get_deal(db: Session, deal_id: int) -> Deal:
    deal = db.get(Deal, deal_id)
    if deal is None:
        raise HTTPException(status_code=404, detail=f"Deal {deal_id} not found")
    return deal


@router.get("/status/{backend_deal_id}", response_model=DealLifecycleSummary)
def lifecycle_status(backend_deal_id: int, db: Session = Depends(get_db)) -> DealLifecycleSummary:
    _get_deal(db, backend_deal_id)
    finished = {"lead_created", "backend_deal_created"}
    if linked_brief(db, backend_deal_id):
        finished.add("deal_brief_created")
    for (event_type,) in db.query(AuditLog.event_type).filter(AuditLog.deal_id == backend_deal_id):
        stage = ACTION_STAGE.get(event_type.removeprefix("lifecycle:")) if event_type.startswith("lifecycle:") else None
        if stage:
            finished.add(stage)
    current = next(stage for stage in reversed(LIFECYCLE_STAGES) if stage in finished)
    pos = LIFECYCLE_STAGES.index(current)
    actions = ["run_underwriting"] if "underwriting_complete" not in finished else ["match_buyers", "prepare_closing"]
    if "closing_context_ready" in finished:
        actions.append("generate_playbook")
    return DealLifecycleSummary(
        backend_deal_id=backend_deal_id, current_stage=current,
        next_recommended_stage=LIFECYCLE_STAGES[pos + 1] if pos + 1 < len(LIFECYCLE_STAGES) else None,
        automated_actions_available=actions,
        steps=[LifecycleStep(name=stage, status="completed" if stage in finished else "pending") for stage in LIFECYCLE_STAGES],
    )


@router.post("/run_action", response_model=RunLifecycleActionResponse)
def run_action(payload: RunLifecycleActionRequest, db: Session = Depends(get_db)) -> RunLifecycleActionResponse:
    action, deal_id, inputs = payload.action, payload.backend_deal_id, payload.inputs
    if action not in ACTION_STAGE:
        raise HTTPException(status_code=400, detail=f"Unknown action '{action}'")
    _get_deal(db, deal_id)
    try:
        match action:
            case "run_underwriting":
                request = UnderwriteDealRequest.model_validate({
                    "deal": {**inputs.get("deal", {}), "deal_id": deal_id}, "policy": inputs.get("policy"),
                })
                output = apply_underwriting(request, db).model_dump(mode="json")
            case "match_buyers":
                brief = linked_brief(db, deal_id)
                if brief is None:
                    raise HTTPException(status_code=409, detail="Linked deal brief required for matching")
                output = {"matched_buyers": [buyer.model_dump(mode="json") for buyer in _find_top_buyers(db, brief)]}
            case "prepare_closing":
                output = get_closing_context(deal_id, db).model_dump(mode="json")
            case "generate_playbook":
                playbook = get_closing_playbook(deal_id, db)
                output = {**playbook, "context": playbook["context"].model_dump(mode="json")}
            case "notify_parties":
                request = NotifyDealPartiesRequest.model_validate({**inputs, "backend_deal_id": deal_id})
                output = prepare_deal_notifications(request, db).model_dump(mode="json")
            case "profit_allocation":
                request = RunProfitAllocationRequest.model_validate({
                    "profit": {**inputs.get("profit", {}), "backend_deal_id": deal_id}, "policy": inputs.get("policy"),
                })
                output = calculate_profit_allocation(request, db).model_dump(mode="json")
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail="Valid action inputs are required") from exc

    # Keep the decision/result details in their authoritative service records.
    # The lifecycle receipt marks the completed internal action only.
    db.add(AuditLog(
        deal_id=deal_id, event_type=f"lifecycle:{action}", event_source="system",
        message="Internal lifecycle action completed", event_data=json.dumps({"external_effects": False}),
    ))
    db.commit()
    return RunLifecycleActionResponse(
        backend_deal_id=deal_id, action=action, status="success",
        message="Internal action completed.", output=output,
    )
