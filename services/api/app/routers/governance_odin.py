# services/api/app/routers/governance_odin.py

from __future__ import annotations

from decimal import Decimal
from typing import List

from fastapi import APIRouter, status

from app.schemas.governance import (
    OdinPolicy,
    KingEvaluationContext,  # generic context
    KingDecision,           # generic decision shape
)

router = APIRouter(
    prefix="/governance",
    tags=["Governance", "Odin"],
)

ODIN_POLICY = OdinPolicy()


def _to_decimal(val, default: Decimal = Decimal("0")) -> Decimal:
    try:
        return Decimal(str(val))
    except Exception:
        return default


def _to_int(val, default: int = 0) -> int:
    try:
        return int(val)
    except Exception:
        return default


def evaluate_vertical_limits(policy: OdinPolicy, data: dict) -> List[str]:
    """
    Checks if you're spreading Valhalla across too many major verticals.
    """
    reasons: List[str] = []

    active_verticals = _to_int(data.get("active_verticals"))
    new_verticals = _to_int(data.get("new_verticals"), 1)
    total_after = active_verticals + new_verticals

    if total_after > policy.strategy.max_active_verticals:
        reasons.append(
            f"Total verticals after expansion ({total_after}) exceeds Odin's limit "
            f"of {policy.strategy.max_active_verticals} active verticals."
        )

    return reasons


def evaluate_profit_vs_complexity(policy: OdinPolicy, data: dict) -> List[str]:
    """
    Evaluates whether the proposed project/vertical actually pulls its weight.
    """
    reasons: List[str] = []

    est_annual_profit = _to_decimal(data.get("estimated_annual_profit"))
    complexity_score = _to_int(data.get("complexity_score"))  # 1-10
    break_even_months = _to_int(data.get("time_to_break_even_months"))

    if est_annual_profit < policy.strategy.min_estimated_annual_profit:
        reasons.append(
            f"Estimated annual profit {est_annual_profit} is below Odin's minimum "
            f"{policy.strategy.min_estimated_annual_profit}."
        )

    if complexity_score > policy.strategy.max_complexity_score:
        reasons.append(
            f"Complexity score {complexity_score}/10 exceeds Odin's max of "
            f"{policy.strategy.max_complexity_score}/10."
        )

    if break_even_months > policy.strategy.max_time_to_break_even_months:
        reasons.append(
            f"Break-even time {break_even_months} months exceeds Odin's limit of "
            f"{policy.strategy.max_time_to_break_even_months} months."
        )

    return reasons


def evaluate_mission_criticality(data: dict) -> List[str]:
    """
    Odin prefers mission-critical projects over distractions.
    """
    reasons: List[str] = []

    mission_critical = bool(data.get("mission_critical"))
    distraction_score = _to_int(data.get("distraction_score"), 0)  # 0-10

    if not mission_critical and distraction_score >= 7:
        reasons.append(
            "Project is not mission-critical and has a high distraction score "
            f"({distraction_score}/10). Odin views this as a distraction from the main path."
        )

    return reasons


@router.post(
    "/odin/evaluate",
    response_model=KingDecision,
    status_code=status.HTTP_200_OK,
    summary="Odin evaluation: strategy, focus, and expansion",
    description=(
        "Odin evaluates big decisions: new business verticals, large projects, or "
        "major experiments. He looks at annual profit, complexity, break-even, "
        "vertical count, and whether it's mission-critical or a distraction."
    ),
)
def evaluate_odin(payload: KingEvaluationContext) -> KingDecision:
    data = payload.data
    policy = ODIN_POLICY

    vertical_reasons = evaluate_vertical_limits(policy, data)
    profit_complexity_reasons = evaluate_profit_vs_complexity(policy, data)
    mission_reasons = evaluate_mission_criticality(data)

    all_reasons = vertical_reasons + profit_complexity_reasons + mission_reasons

    if not all_reasons:
        return KingDecision(
            allowed=True,
            severity="info",
            reasons=[],
            notes="Odin approves this from a strategic perspective.",
        )

    # Decide severity
    severity = "warn"
    for r in all_reasons:
        if "exceeds Odin's limit" in r or "distraction from the main path" in r:
            severity = "critical"
            break

    allowed = severity != "critical"

    return KingDecision(
        allowed=allowed,
        severity=severity,
        reasons=all_reasons,
        notes=(
            "Odin allows with strategic warnings."
            if allowed and severity == "warn"
            else "Odin denies; not aligned with strategic focus or constraints."
        ),
    )
