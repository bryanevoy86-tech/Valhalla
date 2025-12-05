# services/api/app/routers/flow_funfunds_presets.py

from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, status

from app.schemas.funfunds_planner import (
    FunFundsPlanInput,
    FunFundsPlanResponse,
)
from app.routers.flow_funfunds_planner import _compute_allocation, _round_money

router = APIRouter(
    prefix="/flow",
    tags=["Flow", "FunFundsPresets"],
)


def _build_base_input(
    month_label: str,
    gross_income: float,
    fixed_bills: list[dict],
) -> FunFundsPlanInput:
    return FunFundsPlanInput(
        month_label=month_label,
        gross_income=gross_income,
        fixed_bills=fixed_bills,
    )


@router.post(
    "/funfunds_plan/lean",
    response_model=FunFundsPlanResponse,
    status_code=status.HTTP_200_OK,
    summary="Lean mode FunFunds plan (safety + debt priority)",
    description=(
        "Preset plan tuned for 'lean' months:\n"
        "- higher safety reserve\n"
        "- higher debt paydown\n"
        "- modest FunFunds\n"
        "- modest reinvestment\n"
        "You still provide income + bills; the dials are preconfigured."
    ),
)
def compute_funfunds_lean(
    payload: FunFundsPlanInput,
) -> FunFundsPlanResponse:
    # Override dials for lean mode
    payload.min_safety_reserve_percent = Decimal("0.20")
    payload.funfunds_percent = Decimal("0.10")
    payload.debt_paydown_percent = Decimal("0.30")
    payload.reinvest_percent = Decimal("0.30")

    allocation, flags = _compute_allocation(payload)
    net_after_bills = _round_money(payload.gross_income - allocation.bills_total)

    debug = {
        "mode": "lean",
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


@router.post(
    "/funfunds_plan/growth",
    response_model=FunFundsPlanResponse,
    status_code=status.HTTP_200_OK,
    summary="Growth mode FunFunds plan (machine + play priority)",
    description=(
        "Preset plan tuned for 'growth mode' months:\n"
        "- normal safety reserve\n"
        "- decent FunFunds\n"
        "- moderate debt paydown\n"
        "- aggressive reinvestment into the machine."
    ),
)
def compute_funfunds_growth(
    payload: FunFundsPlanInput,
) -> FunFundsPlanResponse:
    # Override dials for growth mode
    payload.min_safety_reserve_percent = Decimal("0.10")
    payload.funfunds_percent = Decimal("0.20")
    payload.debt_paydown_percent = Decimal("0.15")
    payload.reinvest_percent = Decimal("0.45")

    allocation, flags = _compute_allocation(payload)
    net_after_bills = _round_money(payload.gross_income - allocation.bills_total)

    debug = {
        "mode": "growth",
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
