# services/api/app/routers/governance_orchestrator.py

from __future__ import annotations

from typing import Dict, List

from fastapi import APIRouter, HTTPException, status

from app.schemas.governance import (
    GovernanceAggregateDecision,
    GovernanceCheckResult,
    GovernanceEvaluationRequest,
    KingDecision,
    KingEvaluationContext,
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
    # Invoke actual specialist functions in-process, so worker execution
    # does not depend on an HTTP test client or recursively boot the API.
    from app.routers.governance_king import evaluate_king
    from app.routers.governance_queen import evaluate_queen
    from app.routers.governance_odin import evaluate_odin
    from app.routers.governance_loki import evaluate_loki
    from app.routers.governance_tyr import evaluate_tyr

    evaluators = {
        "king": evaluate_king, "queen": evaluate_queen, "odin": evaluate_odin,
        "loki": evaluate_loki, "tyr": evaluate_tyr,
    }
    gods = list(dict.fromkeys(payload.gods or list(evaluators)))
    full_coverage = set(gods) == set(evaluators)

    checks: List[GovernanceCheckResult] = []
    worst_severity = "info"
    overall_allowed = True
    blocked_by: List[str] = []

    for god_name in gods:
        evaluator = evaluators.get(god_name)
        if evaluator is None:
            raise HTTPException(status_code=400, detail="Unknown specialist")
        try:
            decision = KingDecision.model_validate(evaluator(
                KingEvaluationContext(context_type=payload.context_type, data=payload.data)
            ))
        except Exception as exc:
            raise HTTPException(
                status_code=503, detail=f"Specialist {god_name} unavailable"
            ) from exc
        if decision.severity not in {"info", "warn", "critical"}:
            raise HTTPException(status_code=503, detail=f"Invalid specialist result: {god_name}")

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
        if decision.severity.lower() == "critical" or (not decision.allowed and decision.severity.lower() == "info"):
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
        full_coverage=full_coverage,
        evaluation_only=True,
        external_effects_authorized=False,
    )
