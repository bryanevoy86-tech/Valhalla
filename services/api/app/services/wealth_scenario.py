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


# These owner-proposed anchors are recommendations in monthly CAD minor units.
DEFAULT_PERSONAL_ANCHORS = tuple((profit * 100, personal * 100) for profit, personal in (
    (10000, 4000), (25000, 7500), (50000, 12500), (100000, 20000), (150000, 30000),
    (250000, 37500), (500000, 50000), (1000000, 100000), (5000000, 250000),
))


class AllocationAnchor(StrictModel):
    profit_minor: Minor
    personal_minor: Minor


def default_allocation_anchors():
    return [AllocationAnchor(profit_minor=profit, personal_minor=personal)
            for profit, personal in DEFAULT_PERSONAL_ANCHORS]


class PersonalAllocationIn(StrictModel):
    scope: MarketScope
    statement_id: UUID
    anchors: list[AllocationAnchor] = Field(default_factory=default_allocation_anchors, min_length=2, max_length=20)
    essential_household_minor: Minor
    other_household_income_minor: Minor = 0
    personal_reserve_target_minor: Minor
    personal_reserve_balance_minor: Minor
    operating_reserve_minor: Minor
    corporate_tax_reserve_minor: Minor
    additional_obligations_minor: Minor = 0
    owner_monthly_limit_minor: Minor | None = None

    @model_validator(mode="after")
    def ordered_anchors(self):
        previous_profit = previous_personal = 0
        for anchor in self.anchors:
            profit_delta = anchor.profit_minor - previous_profit
            personal_delta = anchor.personal_minor - previous_personal
            if profit_delta <= 0 or not 0 <= personal_delta <= profit_delta:
                raise ValueError("Allocation anchors must increase without allocating more than each profit increment")
            previous_profit, previous_personal = anchor.profit_minor, anchor.personal_minor
        return self


def interpolate_personal(eligible_minor, anchors):
    previous_profit = previous_personal = 0
    for anchor in anchors:
        if eligible_minor <= anchor.profit_minor:
            return previous_personal + (
                (eligible_minor - previous_profit) * (anchor.personal_minor - previous_personal)
                // (anchor.profit_minor - previous_profit)
            )
        previous_profit, previous_personal = anchor.profit_minor, anchor.personal_minor
    return previous_personal


def allocation_waterfall(eligible, request):
    anchor = interpolate_personal(eligible, request.anchors)
    recommended = anchor if request.owner_monthly_limit_minor is None else min(anchor, request.owner_monthly_limit_minor)
    essential_need = max(0, request.essential_household_minor - request.other_household_income_minor)
    essentials = min(recommended, essential_need)
    reserve_need = max(0, request.personal_reserve_target_minor - request.personal_reserve_balance_minor)
    reserve = min(recommended - essentials, reserve_need)
    return {
        "anchor_recommendation_minor": anchor, "recommended_personal_minor": recommended,
        "remaining_eligible_for_reinvestment_minor": eligible - recommended,
        "personal_breakdown": {"essentials_minor": essentials, "reserve_minor": reserve,
                               "remaining_personal_minor": recommended - essentials - reserve},
        "shortfalls": {"essentials_minor": essential_need - essentials, "personal_reserve_minor": reserve_need - reserve},
        "contingency_review_recommended": essentials < essential_need,
    }


def recommend_personal_allocation(db, request: PersonalAllocationIn, today: date):
    from calendar import monthrange

    from fastapi import HTTPException

    from app.loki.evidence import artifact_digest
    from app.models.economic_control import EconomicRecord
    from app.models.treasury_reconciliation import StatementAccount, StatementImport
    from app.routers.economic_control import context, require_schema
    from app.services.economic_control import assessment, verify_checkout_performance
    from app.services.prime_business_execution import _emergency_stop_active
    from app.services.specialist_triggers import outcome_scope_key
    from app.services.treasury_reconciliation import payload_for, statement_ready

    require_schema(db)
    if not statement_ready(db):
        raise HTTPException(503, "Statement evidence is unavailable")
    operation, state, pool = context(db, request.scope, lock=False)
    statement = db.get(StatementImport, request.statement_id)
    account = db.get(StatementAccount, statement.account_key) if statement is not None else None
    if (account is None or account.head_id != request.statement_id or account.purpose != "BUSINESS"
            or account.currency != "CAD" or account.scope_key != outcome_scope_key(operation.scope)
            or operation.currency != "CAD"):
        raise HTTPException(409, "Current scoped CAD business statement is required")
    cash = payload_for(statement)
    performance = state.performance
    if (cash.scope.model_dump() != operation.scope or cash.purpose != "BUSINESS" or cash.currency != "CAD"
            or cash.end != statement.period_end or performance is None or (cash.start, cash.end) !=
            (performance.start, performance.end) or cash.start.day != 1
            or cash.end.day != monthrange(cash.end.year, cash.end.month)[1]
            or (cash.start.year, cash.start.month) != (cash.end.year, cash.end.month)):
        raise HTTPException(409, "Aligned monthly statement and economic evidence are required")
    proof = verify_checkout_performance(db, performance)
    if proof is None:
        raise HTTPException(409, "A verified checkout-linked fixture is required for this rehearsal")
    if not any(item["statement_id"] == str(statement.id) for item in proof["settlements"]):
        raise HTTPException(409, "The scoped cash head must reconcile to the booked checkout fixture")
    economics = assessment(db, operation, state, pool, today)
    blockers = list(economics["blockers"])
    if _emergency_stop_active(db):
        blockers.append("EMERGENCY_STOP")
    recorded_liabilities = max(cash.outstanding_liabilities_minor, economics["open_obligations_minor"])
    protected = (recorded_liabilities + request.additional_obligations_minor + request.corporate_tax_reserve_minor
                 + max(request.operating_reserve_minor, state.mandate.min_operating_reserve)
                 + economics["outstanding_reservations_minor"] + performance.outstanding_exposure)
    profit = max(0, economics["period_net_minor"] - request.corporate_tax_reserve_minor)
    cash_headroom = max(0, cash.closing_minor - protected)
    eligible = 0 if blockers else min(profit, cash_headroom)
    record = db.get(EconomicRecord, performance.id)
    result = {
        "scope": operation.scope, "policy": "DYNAMIC_PERSONAL_ALLOCATION", "currency": "CAD",
        "basis": "RECONCILIATION_FIXTURE", "period": cash.start.isoformat(),
        "statement": {"id": str(statement.id), "sha256": statement.digest},
        "economic_performance": {"id": str(performance.id), "sha256": record.digest, "checkout_sha256": proof["sha256"]},
        "fixture_period_profit_after_tax_reserve_minor": profit, "fixture_cash_headroom_minor": cash_headroom,
        "business_protections_minor": protected, "eligible_distributable_profit_minor": eligible,
        **allocation_waterfall(eligible, request),
        "blockers": sorted(set(blockers)), "expansion_candidates": economics["alternatives"][:5],
        "stretch_objective": {"first_operating_days": 90, "monthly_personal_min_minor": 2000000,
                              "monthly_personal_max_minor": 3000000, "guaranteed": False},
        "requires_independent_review": True, "standing_mandate_approved": False,
        "actual_accessible_funds_minor": None, "funds_movement_authorized": False,
    }
    return {**result, "sha256": artifact_digest("personal_allocation_fixture", str(statement.id),
                                                 {"inputs": request.model_dump(mode="json"), "result": result})}
