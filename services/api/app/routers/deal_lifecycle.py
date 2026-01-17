# services/api/app/routers/deal_lifecycle.py

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.deal import Deal
from app.schemas.deal_lifecycle import (
    DealLifecycleSummary,
    LifecycleStep,
    RunLifecycleActionRequest,
    RunLifecycleActionResponse,
)

# We will call internal flow endpoints
from app.main import app as main_app

client = TestClient(main_app)

router = APIRouter(
    prefix="/lifecycle",
    tags=["Lifecycle"],
)

# Static lifecycle definition (Year-1)
LIFECYCLE_STAGES = [
    "lead_created",
    "deal_brief_created",
    "backend_deal_created",
    "underwriting_complete",
    "buyer_matching_complete",
    "closing_context_ready",
    "closing_call_started",
    "closing_call_completed",
    "profit_realized",
]

# Map actions → API calls
ACTION_MAP = {
    "run_underwriting": {
        "method": "post",
        "path": "/flow/underwrite_deal"
    },
    "match_buyers": {
        "method": "post",
        "path": "/flow/full_deal_pipeline"  # full pipeline includes buyer match
    },
    "prepare_closing": {
        "method": "get",
        "path": "/flow/closing_context/{id}"
    },
    "generate_playbook": {
        "method": "get",
        "path": "/flow/closing_playbook/{id}"
    },
    "notify_parties": {
        "method": "post",
        "path": "/flow/notify_deal_parties"
    },
    "profit_allocation": {
        "method": "post",
        "path": "/flow/profit_allocation"
    },
}


def _detect_stage(deal: Deal) -> str:
    """
    Best-effort stage detection using the fields we have.
    """
    if not deal.lead_id:
        return "lead_created"

    # BRIEF / BACKEND DEAL Linking
    if deal.offer is None:
        return "backend_deal_created"

    # UNDERWRITING indicators
    if deal.mao:
        return "underwriting_complete"

    # If we have ROI notes or underwriting meta
    if getattr(deal, "roi_note", None):
        return "underwriting_complete"

    return "lead_created"


def _empty_steps(backend_deal_id: int, stage: str) -> List[LifecycleStep]:
    steps = []
    for s in LIFECYCLE_STAGES:
        steps.append(LifecycleStep(
            name=s,
            status=("completed" if LIFECYCLE_STAGES.index(s) <= LIFECYCLE_STAGES.index(stage) else "pending")
        ))
    return steps


@router.get(
    "/status/{backend_deal_id}",
    response_model=DealLifecycleSummary,
    summary="Unified lifecycle summary for a deal",
)
def lifecycle_status(
    backend_deal_id: int,
    db: Session = Depends(get_db),
) -> DealLifecycleSummary:
    deal = db.query(Deal).filter(Deal.id == backend_deal_id).first()
    if not deal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deal {backend_deal_id} not found."
        )

    current_stage = _detect_stage(deal)
    steps = _empty_steps(backend_deal_id, current_stage)

    # Next recommended stage
    idx = LIFECYCLE_STAGES.index(current_stage)
    next_stage = LIFECYCLE_STAGES[idx + 1] if idx + 1 < len(LIFECYCLE_STAGES) else None

    # Allowed auto-actions based on stage
    allowed = []
    if current_stage == "backend_deal_created":
        allowed.append("run_underwriting")
    if current_stage == "underwriting_complete":
        allowed.append("match_buyers")
        allowed.append("prepare_closing")
    if current_stage == "closing_context_ready":
        allowed.append("generate_playbook")
        allowed.append("closing_call_started")

    return DealLifecycleSummary(
        backend_deal_id=backend_deal_id,
        steps=steps,
        current_stage=current_stage,
        next_recommended_stage=next_stage,
        automated_actions_available=allowed,
    )


@router.post(
    "/run_action",
    response_model=RunLifecycleActionResponse,
    summary="Run an automated lifecycle action for a deal",
    description="Runs an internal API call for underwriting, matching, closing prep, notifications, or profit allocation.",
)
def run_action(
    payload: RunLifecycleActionRequest,
    db: Session = Depends(get_db),
) -> RunLifecycleActionResponse:

    action = payload.action
    backend_deal_id = payload.backend_deal_id

    if action not in ACTION_MAP:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown action '{action}'. Valid actions: {list(ACTION_MAP.keys())}"
        )

    cfg = ACTION_MAP[action]
    method = cfg["method"]
    path = cfg["path"]

    # Format path
    if "{id}" in path:
        path = path.replace("{id}", str(backend_deal_id))

    # Prepare payload for the action
    if action == "notify_parties":
        req = {
            "backend_deal_id": backend_deal_id,
            "include_seller": True,
            "include_buyers": True,
            "min_buyer_score": 0.5,
            "max_buyers": 10
        }
        resp = client.post(path, json=req)
    elif action == "profit_allocation":
        req = {
            "profit": {
                "backend_deal_id": backend_deal_id,
                "sale_price": 350000,
                "sale_closing_costs": 15000,
                "extra_expenses": 5000,
                "tax_rate": 0.25,
                "funfunds_percent": 0.15,
                "reinvest_percent": 0.50,
            }
        }
        resp = client.post(path, json=req)
    else:
        # GET or bare POST
        if method == "get":
            resp = client.get(path)
        else:
            resp = client.post(path, json={"backend_deal_id": backend_deal_id})

    if resp.status_code not in (200, 201):
        raise HTTPException(
            status_code=500,
            detail=f"Action '{action}' failed: {resp.status_code} – {resp.text}"
        )

    return RunLifecycleActionResponse(
        backend_deal_id=backend_deal_id,
        action=action,
        status="success",
        message=f"Action '{action}' executed successfully.",
        output=resp.json(),
    )
