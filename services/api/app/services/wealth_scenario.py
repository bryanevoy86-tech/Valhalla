"""Owner-private household and treasury scenario arithmetic in integer minor units."""
from datetime import date
from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field, model_validator

from app.schemas.market_intelligence import MarketScope, StrictModel

Minor = Annotated[int, Field(strict=True, ge=0, le=10_000_000_000)]
Category = Literal["HOUSING", "FOOD", "UTILITIES", "TRANSPORT", "CHILDCARE", "DEBT", "INSURANCE", "OTHER"]


class HouseholdLine(StrictModel):
    category: Category
    budget_minor: Minor
    expenditure_minor: Minor


class WealthScenario(StrictModel):
    scenario_id: UUID
    scope: MarketScope
    month: date
    currency: Literal["CAD", "USD", "EUR", "GBP"]
    years_from_launch: int = Field(strict=True, ge=1, le=100)
    evidence_class: Literal["OWNER_REPORTED", "ASSUMPTION"]
    net_business_cash_minor: Minor
    available_operating_reserve_minor: Minor
    target_operating_reserve_minor: Minor
    target_owner_compensation_minor: Minor
    other_household_income_minor: Minor
    fun_fund_cap_minor: Minor
    simulate_withdrawal: bool = Field(strict=True)
    household_lines: list[HouseholdLine] = Field(min_length=1, max_length=8)

    @model_validator(mode="after")
    def valid_month_and_categories(self):
        if self.month.day != 1 or len({line.category for line in self.household_lines}) != len(self.household_lines):
            raise ValueError("Use the first day of the month and a unique household category per line")
        return self


def project_household_and_treasury(plan: WealthScenario) -> dict:
    cash = plan.net_business_cash_minor
    gap = max(0, plan.target_operating_reserve_minor - plan.available_operating_reserve_minor)
    reserve = min(gap, cash)
    compensation = min(plan.target_owner_compensation_minor, cash - reserve)
    allocatable_cash = cash - reserve - compensation
    fun_accrual = allocatable_cash // 10
    release = min(plan.fun_fund_cap_minor, fun_accrual) if plan.years_from_launch > 1 and plan.simulate_withdrawal else 0
    expenses = sum(line.expenditure_minor for line in plan.household_lines)
    budget = sum(line.budget_minor for line in plan.household_lines)
    income = plan.other_household_income_minor + compensation
    return {
        "basis": "INTERNAL_SCENARIO", "currency": plan.currency,
        "policy_order": ["OPERATING_RESERVE", "PLANNED_COMPENSATION", "90_10_ALLOCATABLE_SURPLUS"],
        "operating_reserve_addition_minor": reserve,
        "unfunded_reserve_target_minor": gap - reserve,
        "planned_owner_compensation_minor": compensation,
        "unfunded_owner_compensation_minor": plan.target_owner_compensation_minor - compensation,
        "planned_reinvestment_minor": allocatable_cash - fun_accrual,
        "fun_fund_accrual_minor": fun_accrual,
        "modeled_fun_fund_withdrawal_minor": release,
        "tracked_fun_fund_retained_minor": fun_accrual - release,
        "household": {
            "planned_income_minor": income, "budget_minor": budget, "expenditure_minor": expenses,
            "income_less_expenditure_minor": income - expenses, "budget_less_expenditure_minor": budget - expenses,
            "lines": [{**line.model_dump(), "budget_less_expenditure_minor": line.budget_minor - line.expenditure_minor}
                      for line in plan.household_lines],
        },
        "funds_movement_authorized": False, "verified_results": False,
    }
