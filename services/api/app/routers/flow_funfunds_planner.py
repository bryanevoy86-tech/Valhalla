# services/api/app/routers/flow_funfunds_planner.py

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Tuple

from fastapi import APIRouter, status
from app.schemas.funfunds_planner import (
    FunFundsAllocation,
    FunFundsPlanInput,
    FunFundsPlanResponse,
    FunFundsPolicyFlags,
)

router = APIRouter(
    prefix="/flow",
    tags=["Flow", "FunFunds"],
)


def _round_money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _compute_allocation(input_data: FunFundsPlanInput) -> Tuple[FunFundsAllocation, FunFundsPolicyFlags]:
    # 1. Basic sums
    bills_total = sum((bill.amount for bill in input_data.fixed_bills), start=Decimal("0"))
    bills_total = _round_money(bills_total)

    net_after_bills = _round_money(input_data.gross_income - bills_total)

    # If there is nothing left after bills, everything else is zero.
    if net_after_bills <= 0:
        allocation = FunFundsAllocation(
            bills_total=bills_total,
            safety_reserve=Decimal("0"),
            funfunds_amount=Decimal("0"),
            debt_paydown_amount=Decimal("0"),
            reinvest_amount=Decimal("0"),
            leftover_amount=Decimal("0"),
        )
        flags = FunFundsPolicyFlags(
            breach_safety_minimum=True,
            notes="No net income after bills; unable to fund safety, FunFunds, or reinvestment.",
        )
        return allocation, flags

    # 2. Raw allocations from requested percents
    safety_min = _round_money(net_after_bills * input_data.min_safety_reserve_percent)
    funfunds_raw = net_after_bills * input_data.funfunds_percent
    debt_raw = net_after_bills * input_data.debt_paydown_percent
    reinvest_raw = net_after_bills * input_data.reinvest_percent

    total_raw = funfunds_raw + debt_raw + reinvest_raw

    # 3. If total_raw > (net_after_bills - safety_min), scale down proportionally
    available_for_dials = net_after_bills - safety_min
    if available_for_dials < 0:
        available_for_dials = Decimal("0")

    flags = FunFundsPolicyFlags(breach_safety_minimum=False, notes=None)

    if total_raw <= available_for_dials or total_raw == 0:
        # No scaling needed
        funfunds = _round_money(funfunds_raw)
        debt = _round_money(debt_raw)
        reinvest = _round_money(reinvest_raw)
    else:
        scale = available_for_dials / total_raw
        funfunds = _round_money(funfunds_raw * scale)
        debt = _round_money(debt_raw * scale)
        reinvest = _round_money(reinvest_raw * scale)
        flags.notes = (
            "Requested allocation exceeded available net after bills and safety reserve; "
            "scaled FunFunds, debt, and reinvestment down proportionally."
        )

    used = safety_min + funfunds + debt + reinvest
    leftover = _round_money(net_after_bills - used)

    # If leftover is negative due to rounding, push that into reinvest (last bucket).
    if leftover < 0:
        reinvest = _round_money(reinvest + leftover)
        leftover = Decimal("0")

    allocation = FunFundsAllocation(
        bills_total=bills_total,
        safety_reserve=safety_min,
        funfunds_amount=funfunds,
        debt_paydown_amount=debt,
        reinvest_amount=reinvest,
        leftover_amount=leftover,
    )

    # If safety reserve ended up being less than a small threshold of net_after_bills, flag it.
    # Here we just use the configured minimum; if net is tiny, this may be effectively zero.
    if safety_min < net_after_bills * input_data.min_safety_reserve_percent:
        # Usually not hit because we set safety_min from that expression,
        # but left here for future extension when safety is more dynamic.
        pass

    return allocation, flags


@router.post(
    "/funfunds_plan",
    response_model=FunFundsPlanResponse,
    status_code=status.HTTP_200_OK,
    summary="Compute monthly FunFunds + reinvestment plan",
    description=(
        "Given monthly income and bills, computes how much goes to:\n"
        "- fixed bills\n"
        "- safety reserve\n"
        "- FunFunds (play money)\n"
        "- debt paydown\n"
        "- reinvestment into the machine\n"
        "- leftover buffer\n"
        "according to your Valhalla dial settings."
    ),
)
def compute_funfunds_plan(
    payload: FunFundsPlanInput,
) -> FunFundsPlanResponse:
    allocation, flags = _compute_allocation(payload)

    net_after_bills = _round_money(payload.gross_income - allocation.bills_total)

    debug = {
        "gross_income": str(payload.gross_income),
        "bills_total": str(allocation.bills_total),
        "net_after_bills": str(net_after_bills),
        "min_safety_reserve_percent": str(payload.min_safety_reserve_percent),
        "funfunds_percent": str(payload.funfunds_percent),
        "debt_paydown_percent": str(payload.debt_paydown_percent),
        "reinvest_percent": str(payload.reinvest_percent),
    }

    return FunFundsPlanResponse(
        month_label=payload.month_label,
        gross_income=payload.gross_income,
        bills_total=allocation.bills_total,
        net_after_bills=net_after_bills,
        allocation=allocation,
        policy_flags=flags,
        debug=debug,
    )
