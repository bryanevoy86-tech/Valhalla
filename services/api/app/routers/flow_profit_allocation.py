# services/api/app/routers/flow_profit_allocation.py

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Tuple

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.deal import Deal
from app.schemas.profit_allocation import (
    ProfitAllocationBreakdown,
    ProfitAllocationFlags,
    ProfitAllocationMetrics,
    ProfitAllocationPolicy,
    ProfitAllocationResult,
    RunProfitAllocationRequest,
    RunProfitAllocationResponse,
)
from app.services.freeze_events import log_freeze_event

router = APIRouter(
    prefix="/flow",
    tags=["Flow", "ProfitAllocation"],
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


def _round_money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _compute_metrics(
    deal: Deal,
    sale_price: Decimal,
    sale_closing_costs: Decimal,
    extra_expenses: Decimal,
    tax_rate: Decimal,
) -> ProfitAllocationMetrics:
    purchase_price = _decimal(getattr(deal, "offer", None) or getattr(deal, "price", None))
    repairs = _decimal(getattr(deal, "repairs", None))
    # For now, assume entry closing costs are folded into extra_expenses or repairs.
    entry_closing_costs = Decimal("0")

    total_cost_basis = purchase_price + repairs + entry_closing_costs

    gross_profit = sale_price - (total_cost_basis + sale_closing_costs + extra_expenses)

    if gross_profit <= 0:
        taxes = Decimal("0")
    else:
        taxes = _round_money(gross_profit * tax_rate)

    net_profit_after_tax = gross_profit - taxes

    return ProfitAllocationMetrics(
        purchase_price=_round_money(purchase_price),
        repairs=_round_money(repairs),
        entry_closing_costs=_round_money(entry_closing_costs),
        total_cost_basis=_round_money(total_cost_basis),
        sale_price=_round_money(sale_price),
        sale_closing_costs=_round_money(sale_closing_costs),
        extra_expenses=_round_money(extra_expenses),
        gross_profit=_round_money(gross_profit),
        taxes=_round_money(taxes),
        net_profit_after_tax=_round_money(net_profit_after_tax),
    )


def _apply_policy_to_net(
    metrics: ProfitAllocationMetrics,
    policy: ProfitAllocationPolicy,
    funfunds_percent: Decimal,
    reinvest_percent: Decimal,
) -> Tuple[ProfitAllocationBreakdown, ProfitAllocationFlags]:
    flags = ProfitAllocationFlags()
    notes = []

    # Check policy thresholds
    # tax_rate check is done at caller level using debug; here we care about percents.
    if funfunds_percent > policy.max_funfunds_percent:
        flags.breach_funfunds_cap = True
        notes.append(
            f"FunFunds share {funfunds_percent:.1%} exceeds "
            f"max {policy.max_funfunds_percent:.1%}."
        )
    if reinvest_percent < policy.min_reinvest_percent:
        flags.breach_min_reinvest = True
        notes.append(
            f"Reinvest share {reinvest_percent:.1%} is below "
            f"min {policy.min_reinvest_percent:.1%}."
        )

    net = metrics.net_profit_after_tax
    if net <= 0:
        breakdown = ProfitAllocationBreakdown(
            funfunds_amount=Decimal("0"),
            reinvest_amount=Decimal("0"),
            owner_draw_amount=Decimal("0"),
            leftover_amount=Decimal("0"),
        )
        flags.notes = "No net profit after tax; nothing to allocate."
        return breakdown, flags

    ff_amount = _round_money(net * funfunds_percent)
    reinvest_amount = _round_money(net * reinvest_percent)
    # Owner draw gets whatever is left
    owner_draw_amount = _round_money(net - ff_amount - reinvest_amount)
    # Leftover due to rounding / weird config
    leftover_amount = _round_money(net - ff_amount - reinvest_amount - owner_draw_amount)

    breakdown = ProfitAllocationBreakdown(
        funfunds_amount=ff_amount,
        reinvest_amount=reinvest_amount,
        owner_draw_amount=owner_draw_amount,
        leftover_amount=leftover_amount,
    )

    flags.notes = " ".join(notes)
    return breakdown, flags


@router.post(
    "/profit_allocation",
    response_model=RunProfitAllocationResponse,
    status_code=status.HTTP_200_OK,
    summary="Run profit allocation (tax, FunFunds, reinvest, owner draw) for a deal",
    description=(
        "Given a backend_deal_id and sale numbers, compute gross and net profit, "
        "apply tax, and allocate post-tax profit into FunFunds, reinvestment, and "
        "owner draw according to policy."
    ),
)
def run_profit_allocation(
    payload: RunProfitAllocationRequest,
    db: Session = Depends(get_db),
) -> RunProfitAllocationResponse:
    p = payload.profit
    policy = payload.policy or ProfitAllocationPolicy()

    # 1. Load deal
    deal = db.query(Deal).filter(Deal.id == p.backend_deal_id).first()
    if deal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deal with id {p.backend_deal_id} not found.",
        )

    sale_price = _decimal(p.sale_price)
    sale_closing_costs = _decimal(p.sale_closing_costs)
    extra_expenses = _decimal(p.extra_expenses)
    tax_rate = _decimal(p.tax_rate)
    funfunds_percent = _decimal(p.funfunds_percent)
    reinvest_percent = _decimal(p.reinvest_percent)

    # 2. Compute core metrics
    metrics = _compute_metrics(
        deal=deal,
        sale_price=sale_price,
        sale_closing_costs=sale_closing_costs,
        extra_expenses=extra_expenses,
        tax_rate=tax_rate,
    )

    # 3. Policy checks
    flags = ProfitAllocationFlags()
    notes = []

    if tax_rate < policy.min_tax_rate and metrics.gross_profit > 0:
        flags.breach_min_tax_rate = True
        notes.append(
            f"Tax rate {tax_rate:.1%} is below policy minimum {policy.min_tax_rate:.1%}."
        )

    # 4. Allocation
    breakdown, alloc_flags = _apply_policy_to_net(
        metrics=metrics,
        policy=policy,
        funfunds_percent=funfunds_percent,
        reinvest_percent=reinvest_percent,
    )

    # Merge flags
    flags.breach_funfunds_cap = alloc_flags.breach_funfunds_cap
    flags.breach_min_reinvest = alloc_flags.breach_min_reinvest
    combined_notes = notes + ([alloc_flags.notes] if alloc_flags.notes else [])
    flags.notes = " ".join(combined_notes).strip()

    # 5. Build summary + debug
    if metrics.gross_profit <= 0:
        summary = (
            f"Deal {deal.id}: no positive gross profit after sale; "
            "allocation is informational only."
        )
    else:
        summary = (
            f"Deal {deal.id}: gross profit {metrics.gross_profit}, taxes "
            f"{metrics.taxes}, net after tax {metrics.net_profit_after_tax}. "
            f"Allocated FunFunds {breakdown.funfunds_amount}, reinvest "
            f"{breakdown.reinvest_amount}, owner draw {breakdown.owner_draw_amount}."
        )

    debug = {
        "tax_rate": str(tax_rate),
        "funfunds_percent": str(funfunds_percent),
        "reinvest_percent": str(reinvest_percent),
    }

    result = ProfitAllocationResult(
        metrics=metrics,
        breakdown=breakdown,
        policy=policy,
        flags=flags,
        summary=summary,
        debug=debug,
    )

    # 6. Freeze event if serious policy breach
    freeze_event_created = False
    if (
        flags.breach_min_tax_rate
        or flags.breach_funfunds_cap
        or flags.breach_min_reinvest
    ):
        severity = "critical" if flags.breach_min_tax_rate else "warn"
        reason_parts = []
        if flags.breach_min_tax_rate:
            reason_parts.append("Tax rate below policy minimum.")
        if flags.breach_funfunds_cap:
            reason_parts.append("FunFunds allocation above policy cap.")
        if flags.breach_min_reinvest:
            reason_parts.append("Reinvest allocation below policy minimum.")
        reason = " ".join(reason_parts)

        log_freeze_event(
            db=db,
            source="profit_allocation",
            event_type="profit_policy_violation",
            severity=severity,
            reason=reason,
            payload={
                "backend_deal_id": deal.id,
                "gross_profit": str(metrics.gross_profit),
                "taxes": str(metrics.taxes),
                "net_profit_after_tax": str(metrics.net_profit_after_tax),
                "funfunds_amount": str(breakdown.funfunds_amount),
                "reinvest_amount": str(breakdown.reinvest_amount),
                "owner_draw_amount": str(breakdown.owner_draw_amount),
                "flags": {
                    "breach_min_tax_rate": flags.breach_min_tax_rate,
                    "breach_funfunds_cap": flags.breach_funfunds_cap,
                    "breach_min_reinvest": flags.breach_min_reinvest,
                },
            },
            notes="Auto-created by profit_allocation flow.",
        )
        freeze_event_created = True

    return RunProfitAllocationResponse(
        backend_deal_id=deal.id,
        result=result,
        freeze_event_created=freeze_event_created,
    )
