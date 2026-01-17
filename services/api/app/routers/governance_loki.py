# services/api/app/routers/governance_loki.py

from __future__ import annotations

from decimal import Decimal
from typing import List

from fastapi import APIRouter, status

from app.schemas.governance import (
    LokiPolicy,
    KingEvaluationContext,  # generic context
    KingDecision,           # generic decision shape
)

router = APIRouter(
    prefix="/governance",
    tags=["Governance", "Loki"],
)

LOKI_POLICY = LokiPolicy()


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


def evaluate_downside(policy: LokiPolicy, data: dict) -> List[str]:
    """
    Checks how bad the downside can be compared to capital at risk.
    Expects:
    - capital_at_risk
    - worst_case_loss
    """
    reasons: List[str] = []

    capital = _to_decimal(data.get("capital_at_risk"))
    worst_case_loss = _to_decimal(data.get("worst_case_loss"))

    if capital <= 0:
        return reasons

    downside_multiplier = worst_case_loss / capital

    if downside_multiplier > policy.risk.max_downside_multiplier:
        reasons.append(
            f"Downside {downside_multiplier:.2f}x capital exceeds Loki's limit "
            f"of {policy.risk.max_downside_multiplier:.2f}x."
        )

    return reasons


def evaluate_ruin_probability(policy: LokiPolicy, data: dict) -> List[str]:
    """
    Checks probability of ruin (going to zero or beyond).
    Expects:
    - probability_of_ruin (0-1)
    """
    reasons: List[str] = []

    p_ruin = _to_decimal(data.get("probability_of_ruin"))

    if p_ruin > policy.risk.max_probability_of_ruin:
        reasons.append(
            f"Probability of ruin {p_ruin:.2%} exceeds Loki's limit of "
            f"{policy.risk.max_probability_of_ruin:.2%}."
        )

    return reasons


def evaluate_correlation(policy: LokiPolicy, data: dict) -> List[str]:
    """
    Checks how correlated this risk is with the rest of the portfolio.
    Expects:
    - correlation_with_portfolio (0-1)
    """
    reasons: List[str] = []

    corr = _to_decimal(data.get("correlation_with_portfolio"))

    if corr > policy.risk.max_correlation_with_portfolio:
        reasons.append(
            f"Correlation with portfolio {corr:.2%} exceeds Loki's limit of "
            f"{policy.risk.max_correlation_with_portfolio:.2%}."
        )

    return reasons


def evaluate_hidden_complexity(policy: LokiPolicy, data: dict) -> List[str]:
    """
    Checks hidden complexity / unknowns.
    Expects:
    - hidden_complexity_score (1-10)
    """
    reasons: List[str] = []

    hidden_complexity = _to_int(data.get("hidden_complexity_score"))

    if hidden_complexity > policy.risk.max_hidden_complexity_score:
        reasons.append(
            f"Hidden complexity score {hidden_complexity}/10 exceeds Loki's "
            f"limit of {policy.risk.max_hidden_complexity_score}/10."
        )

    return reasons


@router.post(
    "/loki/evaluate",
    response_model=KingDecision,
    status_code=status.HTTP_200_OK,
    summary="Loki evaluation: worst case and hidden risk",
    description=(
        "Loki inverts the view of a deal/project: instead of asking 'how good can this be', "
        "he asks 'how bad can this get?' and 'how likely is ruin or entanglement?'.\n\n"
        "Use this for any high-risk decision: aggressive leverage, new verticals with "
        "unknowns, or deals that feel too good to be true."
    ),
)
def evaluate_loki(payload: KingEvaluationContext) -> KingDecision:
    data = payload.data
    policy = LOKI_POLICY

    downside_reasons = evaluate_downside(policy, data)
    ruin_reasons = evaluate_ruin_probability(policy, data)
    corr_reasons = evaluate_correlation(policy, data)
    complexity_reasons = evaluate_hidden_complexity(policy, data)

    all_reasons = downside_reasons + ruin_reasons + corr_reasons + complexity_reasons

    if not all_reasons:
        return KingDecision(
            allowed=True,
            severity="info",
            reasons=[],
            notes="Loki sees no major hidden downside beyond configured thresholds.",
        )

    severity = "warn"
    # Any of these are strong enough for a hard NO
    for r in all_reasons:
        if (
            "exceeds Loki's limit" in r
            or "probability of ruin" in r
            or "Hidden complexity" in r
        ):
            severity = "critical"
            break

    allowed = severity != "critical"

    return KingDecision(
        allowed=allowed,
        severity=severity,
        reasons=all_reasons,
        notes=(
            "Loki allows with severe caution."
            if allowed and severity == "warn"
            else "Loki denies; downside or entanglement risk is too high."
        ),
    )
