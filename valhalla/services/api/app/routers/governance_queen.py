# services/api/app/routers/governance_queen.py

from __future__ import annotations

from typing import List

from fastapi import APIRouter, status

from app.schemas.governance import (
    QueenPolicy,
    KingEvaluationContext,  # reused as generic evaluation context
    KingDecision,           # reused decision shape
)

router = APIRouter(
    prefix="/governance",
    tags=["Governance", "Queen"],
)

QUEEN_POLICY = QueenPolicy()


def _to_int(val, default: int = 0) -> int:
    try:
        return int(val)
    except Exception:
        return default


def _to_float(val, default: float = 0.0) -> float:
    try:
        return float(val)
    except Exception:
        return default


def evaluate_energy(policy: QueenPolicy, data: dict) -> List[str]:
    """
    Evaluates how this work or project impacts your energy and time.
    """
    reasons: List[str] = []

    hours = _to_int(data.get("hours_per_week"))
    parallel_projects = _to_int(data.get("parallel_projects"))

    if hours > policy.energy.hard_cap_hours_per_week:
        reasons.append(
            f"Requested {hours}h/week exceeds HARD cap of "
            f"{policy.energy.hard_cap_hours_per_week}h/week."
        )
    elif hours > policy.energy.max_hours_per_week:
        reasons.append(
            f"Requested {hours}h/week exceeds preferred max of "
            f"{policy.energy.max_hours_per_week}h/week."
        )

    if parallel_projects > policy.energy.max_parallel_projects:
        reasons.append(
            f"{parallel_projects} parallel projects exceeds Queen's limit of "
            f"{policy.energy.max_parallel_projects}."
        )

    return reasons


def evaluate_family(policy: QueenPolicy, data: dict) -> List[str]:
    """
    Evaluates impact on evenings, weekends, and family space.
    """
    reasons: List[str] = []

    uses_evenings = bool(data.get("uses_evenings"))
    uses_weekends = bool(data.get("uses_weekends"))
    sprint_weeks = _to_int(data.get("sprint_weeks"))

    if policy.family.protect_evenings and uses_evenings:
        reasons.append("Work plan consumes most evenings; Queen prefers evening protection.")

    if policy.family.protect_weekends and uses_weekends:
        reasons.append("Work plan consumes weekends; Queen guards family time on weekends.")

    if sprint_weeks > 4 and policy.family.allow_short_sprints:
        reasons.append(
            f"Sprint longer than 4 weeks ({sprint_weeks} weeks). "
            "Queen only allows short sprints."
        )

    return reasons


def evaluate_stress(policy: QueenPolicy, data: dict) -> List[str]:
    """
    Evaluates stress and emotional load.
    """
    reasons: List[str] = []

    stress_level = _to_int(data.get("stress_level"), default=0)  # 1-10 scale
    chaos_factor = _to_float(data.get("chaos_factor"), default=0.0)  # 0-10 scale

    if stress_level > policy.stress.hard_cap_stress_level:
        reasons.append(
            f"Stress level {stress_level}/10 exceeds HARD cap "
            f"{policy.stress.hard_cap_stress_level}/10."
        )
    elif stress_level > policy.stress.max_stress_level:
        reasons.append(
            f"Stress level {stress_level}/10 exceeds Queen's comfort level "
            f"{policy.stress.max_stress_level}/10."
        )

    if chaos_factor >= 8.0:
        reasons.append(
            f"Chaos factor {chaos_factor}/10 indicates unstable conditions; "
            "Queen is risk-averse to emotional chaos."
        )

    return reasons


@router.post(
    "/queen/evaluate",
    response_model=KingDecision,  # reused shape: allowed/severity/reasons/notes
    status_code=status.HTTP_200_OK,
    summary="Queen evaluation: emotional, family, and burnout governance",
    description=(
        "The Queen evaluates how a plan, deal, project, or build request impacts "
        "your energy, family time, and emotional load. This is where burn-out and "
        "family protection rules live."
    ),
)
def evaluate_queen(payload: KingEvaluationContext) -> KingDecision:
    data = payload.data
    policy = QUEEN_POLICY

    energy_reasons = evaluate_energy(policy, data)
    family_reasons = evaluate_family(policy, data)
    stress_reasons = evaluate_stress(policy, data)

    all_reasons = energy_reasons + family_reasons + stress_reasons

    if not all_reasons:
        return KingDecision(
            allowed=True,
            severity="info",
            reasons=[],
            notes="Queen approves this plan from an energy/family standpoint.",
        )

    # Determine severity
    severity = "warn"
    for r in all_reasons:
        if "HARD cap" in r or "exceeds HARD" in r or "unstable conditions" in r:
            severity = "critical"
            break

    allowed = severity != "critical"

    return KingDecision(
        allowed=allowed,
        severity=severity,
        reasons=all_reasons,
        notes=(
            "Queen allows with caution."
            if allowed and severity == "warn"
            else "Queen denies; plan is not sustainable for you or your family."
        ),
    )
