# services/api/app/routers/governance_orchestrator.py

from __future__ import annotations

from typing import Dict, List

from fastapi import APIRouter, HTTPException, status
from fastapi.testclient import TestClient

from app.schemas.governance import (
    GovernanceAggregateDecision,
    GovernanceCheckResult,
    GovernanceEvaluationRequest,
    KingDecision,
)

router = APIRouter(
    prefix="/governance",
    tags=["Governance", "Pantheon"],
)

GOD_ENDPOINTS: Dict[str, str] = {
    "king": "/api/governance/king/evaluate",
    "queen": "/api/governance/queen/evaluate",
    "odin": "/api/governance/odin/evaluate",
    "loki": "/api/governance/loki/evaluate",
    "tyr": "/api/governance/tyr/evaluate",
}


def _severity_rank(severity: str) -> int:
    severity = (severity or "").lower()
    if severity == "critical":
        return 3
    if severity == "warn":
        return 2
    return 1  # info or unknown


@router.post(
    "/evaluate_all",
    response_model=GovernanceAggregateDecision,
    status_code=status.HTTP_200_OK,
    summary="Evaluate King, Queen, Odin, Loki, and Tyr in one call",
    description=(
        "Runs the full pantheon (or a subset) on a given context and returns a "
        "combined decision: overall allowed/blocked, worst severity, and per-god details."
    ),
)
def evaluate_all(payload: GovernanceEvaluationRequest) -> GovernanceAggregateDecision:
    # Import here to avoid circular imports
    from app.main import app
    
    client = TestClient(app)
    
    gods: List[str] = payload.gods or ["king", "queen", "odin", "loki", "tyr"]

    checks: List[GovernanceCheckResult] = []
    worst_severity = "info"
    overall_allowed = True
    blocked_by: List[str] = []

    for god_name in gods:
        endpoint = GOD_ENDPOINTS.get(god_name)
        if not endpoint:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown god '{god_name}'. Allowed: {list(GOD_ENDPOINTS.keys())}",
            )

        # Reuse the KingEvaluationContext payload shape
        body = {
            "context_type": payload.context_type,
            "data": payload.data,
        }

        resp = client.post(endpoint, json=body)
        if resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Governance endpoint {endpoint} failed: {resp.status_code} {resp.text}",
            )

        decision_raw: dict = resp.json()
        decision = KingDecision.model_validate(decision_raw)

        checks.append(
            GovernanceCheckResult(
                god=god_name,  # type: ignore[arg-type]
                allowed=decision.allowed,
                severity=decision.severity,
                reasons=decision.reasons,
                notes=decision.notes,
            )
        )

        # Track worst severity
        if _severity_rank(decision.severity) > _severity_rank(worst_severity):
            worst_severity = decision.severity

        # Any critical denial forces overall_allowed=False
        if not decision.allowed and decision.severity.lower() == "critical":
            overall_allowed = False
            blocked_by.append(god_name)

    if overall_allowed:
        if worst_severity == "info":
            summary = "All requested gods approve this plan."
        else:
            summary = (
                f"Plan allowed with warnings. Worst severity: {worst_severity}. "
                f"No hard blocks from any god."
            )
    else:
        summary = (
            f"Plan denied. Hard block from: {', '.join(blocked_by)}. "
            f"Worst severity: {worst_severity}."
        )

    return GovernanceAggregateDecision(
        overall_allowed=overall_allowed,
        worst_severity=worst_severity,
        blocked_by=blocked_by,
        checks=checks,
        summary=summary,
    )
