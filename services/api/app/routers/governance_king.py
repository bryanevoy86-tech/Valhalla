# services/api/app/routers/governance_king.py

from __future__ import annotations

from decimal import Decimal
from typing import List

from fastapi import APIRouter, status

from app.schemas.governance import (
    KingPolicy,
    KingEvaluationContext,
    KingDecision,
)

router = APIRouter(
    prefix="/governance",
    tags=["Governance", "King"],
)

# Load default King policy
KING_POLICY = KingPolicy()


def _to_decimal(val) -> Decimal:
    try:
        return Decimal(str(val))
    except Exception:
        return Decimal("0")


def evaluate_risk(policy: KingPolicy, data: dict) -> List[str]:
    """
    Applies universal Valhalla risk rules to ANY deal or project.
    """
    risk_reasons = []

    # Purchase + repair logic
    price = _to_decimal(data.get("purchase_price") or data.get("price"))
    repairs = _to_decimal(data.get("repairs"))
    arv = _to_decimal(data.get("arv"))
    roi = _to_decimal(data.get("roi"))

    # 1. Investment size risk
    if price > policy.risk.max_allowed_investment:
        risk_reasons.append(
            f"Price {price} exceeds max allowed investment {policy.risk.max_allowed_investment}."
        )

    # 2. Repair risk factor
    if price > 0 and repairs > (price * policy.risk.max_repair_risk_factor):
        risk_reasons.append(
            f"Repairs {repairs} exceed {policy.risk.max_repair_risk_factor:.0%} of purchase price."
        )

    # 3. ROI requirement (if provided)
    if roi and roi < policy.risk.min_expected_roi:
        risk_reasons.append(
            f"ROI {roi:.2%} is below minimum expected {policy.risk.min_expected_roi:.2%}."
        )

    # 4. ARV sanity check
    if arv and price and arv < price:
        risk_reasons.append("ARV is lower than purchase price — guaranteed loss.")

    return risk_reasons


def evaluate_values(policy: KingPolicy, data: dict) -> List[str]:
    """
    Checks ethical and mission-alignment values.
    """
    reasons = []

    # Handle both boolean and string values
    predatory = data.get("predatory", False)
    if isinstance(predatory, str):
        predatory = predatory.lower() in ("true", "1", "yes")
    
    environmental_risk = data.get("environmental_risk", False)
    if isinstance(environmental_risk, str):
        environmental_risk = environmental_risk.lower() in ("true", "1", "yes")

    if policy.values.avoid_predatory_tactics and predatory:
        reasons.append("Deal flagged as predatory; King forbids predatory practices.")

    if policy.values.sustainability and environmental_risk:
        reasons.append("Deal flagged as environmentally harmful.")

    return reasons


def evaluate_mission(policy: KingPolicy, data: dict) -> List[str]:
    """
    Checks whether the action aligns with mission priorities.
    """
    reasons = []

    mission_target = data.get("mission_target")

    if mission_target == "equity" and not policy.mission.prioritize_equity_growth:
        reasons.append("Mission conflict: equity growth not prioritized right now.")

    if mission_target == "cashflow" and not policy.mission.prioritize_cashflow:
        reasons.append("Mission conflict: cashflow is not a priority.")

    return reasons


@router.post(
    "/king/evaluate",
    response_model=KingDecision,
    summary="Primary governance endpoint",
    description=(
        "The King evaluates ANY request: deals, profit events, new business ideas, "
        "Heimdall build operations, feature expansions, etc."
    )
)
def evaluate_king(payload: KingEvaluationContext) -> KingDecision:
    data = payload.data
    policy = KING_POLICY

    # Run checks
    risk = evaluate_risk(policy, data)
    values = evaluate_values(policy, data)
    mission = evaluate_mission(policy, data)

    all_reasons = risk + values + mission

    if not all_reasons:
        return KingDecision(
            allowed=True,
            severity="info",
            reasons=[],
            notes="King approves this request."
        )

    # Severity: if any critical reasons, deny
    severity = "warn"
    for r in all_reasons:
        if "forbids" in r.lower() or "guaranteed loss" in r.lower():
            severity = "critical"

    allowed = severity != "critical"

    return KingDecision(
        allowed=allowed,
        severity=severity,
        reasons=all_reasons,
        notes=(
            "King allows with warnings."
            if allowed and severity == "warn"
            else "King denies due to critical issues."
        ),
    )
