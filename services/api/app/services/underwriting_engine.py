# services/api/app/services/underwriting_engine.py

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Tuple

from app.schemas.underwriting_engine import (
    UnderwriteDealRequest,
    UnderwritingDealInput,
    UnderwritingFlags,
    UnderwritingMetrics,
    UnderwritingPolicyConfig,
    UnderwritingResult,
)


def _decimal(value: object | None) -> Decimal:
    if isinstance(value, Decimal):
        return value
    if value is None:
        return Decimal("0")
    try:
        return Decimal(str(value))
    except Exception:
        return Decimal("0")


def _round_pct(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def compute_metrics(deal: UnderwritingDealInput) -> UnderwritingMetrics:
    arv = _decimal(deal.arv)
    purchase = _decimal(deal.purchase_price)
    repairs = _decimal(deal.repairs)
    closing = _decimal(deal.closing_costs)

    # Monthly holding stack
    monthly_stack = (
        _decimal(deal.monthly_taxes)
        + _decimal(deal.monthly_insurance)
        + _decimal(deal.monthly_utilities)
        + _decimal(deal.monthly_hoa)
        + _decimal(deal.monthly_other)
    )
    holding_cost_total = monthly_stack * Decimal(deal.holding_months)

    total_project_cost = purchase + repairs + closing + holding_cost_total

    if arv <= 0:
        equity = Decimal("0")
        equity_pct = Decimal("0")
        ltv = Decimal("0")
    else:
        equity = arv - total_project_cost
        equity_pct = _round_pct(equity / arv)
        ltv = _round_pct(purchase / arv)

    if total_project_cost <= 0:
        roi = Decimal("0")
    else:
        roi = _round_pct(equity / total_project_cost)

    rent_coverage_ratio = None
    if deal.expected_rent is not None and monthly_stack > 0:
        annual_rent = _decimal(deal.expected_rent) * Decimal("12")
        rent_coverage_ratio = _round_pct(annual_rent / (monthly_stack * Decimal("12")))

    return UnderwritingMetrics(
        total_project_cost=total_project_cost,
        equity_amount=equity,
        equity_percent_of_arv=equity_pct,
        ltv=ltv,
        roi=roi,
        holding_cost_total=holding_cost_total,
        rent_coverage_ratio=rent_coverage_ratio,
    )


def apply_policy(
    metrics: UnderwritingMetrics,
    policy: UnderwritingPolicyConfig,
) -> Tuple[UnderwritingFlags, str]:
    flags = UnderwritingFlags(notes="")
    notes = []

    if metrics.ltv > policy.max_ltv:
        flags.breach_ltv = True
        notes.append(
            f"LTV {metrics.ltv:.2%} exceeds max {policy.max_ltv:.2%}."
        )

    if metrics.roi < policy.min_roi:
        flags.breach_roi = True
        notes.append(
            f"ROI {metrics.roi:.2%} is below min {policy.min_roi:.2%}."
        )

    if metrics.equity_percent_of_arv < policy.min_equity_percent:
        flags.breach_equity = True
        notes.append(
            f"Equity {metrics.equity_percent_of_arv:.2%} is below "
            f"min {policy.min_equity_percent:.2%}."
        )

    flags.notes = " ".join(notes)

    # Simple decision tree
    if flags.breach_ltv and flags.breach_roi and flags.breach_equity:
        recommendation = "reject"
    elif flags.breach_ltv or flags.breach_roi or flags.breach_equity:
        recommendation = "renegotiate"
    else:
        recommendation = "offer"

    return flags, recommendation


def run_underwriting(
    request: UnderwriteDealRequest,
) -> UnderwritingResult:
    policy = request.policy or UnderwritingPolicyConfig()
    deal = request.deal

    metrics = compute_metrics(deal)
    flags, recommendation = apply_policy(metrics, policy)

    debug = {
        "strategy": policy.strategy,
        "max_ltv": str(policy.max_ltv),
        "min_roi": str(policy.min_roi),
        "min_equity_percent": str(policy.min_equity_percent),
    }

    return UnderwritingResult(
        metrics=metrics,
        flags=flags,
        recommendation=recommendation,
        policy=policy,
        debug=debug,
    )
