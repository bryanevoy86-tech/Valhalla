"""Owner-private reverse planning over existing allocation policy and scoped Foundry evidence."""
from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import HTTPException
from pydantic import Field, model_validator
from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app.loki.evidence import artifact_digest
from app.models.foundry_evidence import FoundryEvidence
from app.schemas.market_intelligence import StrictModel
from app.services.foundry_discovery import checked_evidence, demand_evidence, economic_blockers, economics
from app.services.wealth_scenario import Minor, PersonalAllocationIn, recommend_personal_allocation


class CommercialCandidate(StrictModel):
    evidence_id: UUID
    in_month_settlement_bp: int = Field(strict=True, ge=0, le=10000)
    fulfillment_limit_units: int = Field(strict=True, ge=0, le=1_000_000)
    units_per_customer: int = Field(strict=True, ge=1, le=1_000_000)
    experiment_budget_minor: Minor


class CommercialTargetsIn(StrictModel):
    allocation: PersonalAllocationIn
    net_personal_target_minor: Annotated[int, Field(strict=True, gt=0, le=10_000_000_000)]
    estimated_personal_tax_bp: int = Field(strict=True, ge=0, lt=10000)
    reserve_addition_minor: Minor
    candidates: list[CommercialCandidate] = Field(min_length=1, max_length=5)

    @model_validator(mode="after")
    def distinct_candidates(self):
        if len({candidate.evidence_id for candidate in self.candidates}) != len(self.candidates):
            raise ValueError("Use distinct Foundry evidence IDs")
        return self


def ceil_div(value: int, divisor: int) -> int:
    return (value + divisor - 1) // divisor


def required_distributable_profit(gross: int, allocation: PersonalAllocationIn) -> int | None:
    if allocation.owner_monthly_limit_minor is not None and gross > allocation.owner_monthly_limit_minor:
        return None
    previous_profit = previous_personal = 0
    for anchor in allocation.anchors:
        if gross <= anchor.personal_minor:
            return previous_profit + ceil_div(
                (gross - previous_personal) * (anchor.profit_minor - previous_profit),
                anchor.personal_minor - previous_personal,
            )
        previous_profit, previous_personal = anchor.profit_minor, anchor.personal_minor
    return None


def candidate_targets(evidence, candidate: CommercialCandidate, request: CommercialTargetsIn,
                      required_profit: int | None, baseline: dict) -> dict:
    measures = economics(evidence)
    demand = demand_evidence(evidence)
    unit_contribution = measures["unit_contribution_minor"]
    settled_unit_receipts = evidence.unit_price * candidate.in_month_settlement_bp // 10000
    unit_cash = settled_unit_receipts - evidence.variable_cost_per_unit - evidence.acquisition_cost_per_unit
    cash_fixed_costs = (evidence.monthly_fixed_cost + request.allocation.corporate_tax_reserve_minor
                        + request.allocation.additional_obligations_minor + request.reserve_addition_minor
                        + (evidence.acquisition.monthly_debt_service if evidence.acquisition else 0))
    blockers = list(baseline["blockers"]) + economic_blockers(evidence.kind, measures)
    if demand is None or not demand["demand_count"]:
        blockers.append("POSITIVE_SOURCED_DEMAND_SAMPLE_MISSING")
    if required_profit is None:
        blockers.append("OWNER_ALLOCATION_POLICY_BELOW_TARGET")
    if unit_contribution <= 0 or unit_cash <= 0:
        blockers.append("NONPOSITIVE_UNIT_MARGIN_OR_IN_MONTH_CASH")
    units = None
    if required_profit is not None and unit_contribution > 0 and unit_cash > 0:
        profit_floor = required_profit + evidence.monthly_fixed_cost + request.allocation.corporate_tax_reserve_minor
        units = max(ceil_div(profit_floor, unit_contribution), ceil_div(required_profit + cash_fixed_costs, unit_cash))
    if units is not None and (units > candidate.fulfillment_limit_units or units > evidence.monthly_units):
        blockers.append("VOLUME_EXCEEDS_DECLARED_DEMAND_OR_FULFILLMENT")
    if evidence.test_cost > candidate.experiment_budget_minor:
        blockers.append("TEST_COST_EXCEEDS_SCENARIO_BUDGET")
    return {
        "evidence_id": str(candidate.evidence_id), "kind": evidence.kind, "revenue_model": evidence.revenue_model,
        "demand_sample_count": demand["sample_count"] if demand else None,
        "required_units": units,
        "required_customers": ceil_div(units, candidate.units_per_customer) if units is not None else None,
        "unit_price_minor": evidence.unit_price,
        "unit_contribution_minor": unit_contribution,
        "required_booked_sales_minor": units * evidence.unit_price if units is not None else None,
        "estimated_in_month_cash_minor": units * settled_unit_receipts if units is not None else None,
        "required_acquisition_budget_minor": units * evidence.acquisition_cost_per_unit if units is not None else None,
        "fulfillment_limit_units": candidate.fulfillment_limit_units,
        "startup_capital_minor": evidence.startup_capital,
        "declared_validation_cost_minor": evidence.test_cost,
        "blockers": sorted(set(blockers)),
    }


def review_commercial_targets(db: Session, request: CommercialTargetsIn, today: date) -> dict:
    baseline = recommend_personal_allocation(db, request.allocation, today)
    scope = request.allocation.scope.model_dump()
    if not inspect(db.connection()).has_table(FoundryEvidence.__tablename__):
        raise HTTPException(503, "Foundry source schema unavailable")
    gross = ceil_div(request.net_personal_target_minor * 10000, 10000 - request.estimated_personal_tax_bp)
    required_profit = required_distributable_profit(gross, request.allocation)
    options = []
    for candidate in request.candidates:
        row = db.get(FoundryEvidence, candidate.evidence_id)
        if row is None:
            raise HTTPException(404, "Scoped Foundry evidence unavailable")
        evidence = checked_evidence(row, scope, today, db=db)
        if evidence.currency != baseline["currency"]:
            raise HTTPException(409, "Foundry currency differs from the scoped statement")
        projection = candidate_targets(evidence, candidate, request, required_profit, baseline)
        options.append({**projection, "foundry_evidence_sha256": row.digest})
    options.sort(key=lambda item: (bool(item["blockers"]), item["startup_capital_minor"],
                                   item["required_acquisition_budget_minor"] or 0, item["evidence_id"]))
    eligible = baseline["eligible_distributable_profit_minor"]
    result = {
        "basis": "SCOPED_RECONCILIATION_FIXTURE_AND_DECLARED_SCENARIOS", "currency": baseline["currency"], "scope": scope,
        "baseline_allocation_sha256": baseline["sha256"], "baseline_statement": baseline["statement"],
        "baseline_performance": baseline["economic_performance"],
        "fixture_eligible_distributable_profit_minor": eligible,
        "fixture_gross_personal_minor": baseline["recommended_personal_minor"],
        "estimated_fixture_after_tax_personal_minor": baseline["recommended_personal_minor"]
        * (10000 - request.estimated_personal_tax_bp) // 10000,
        "net_personal_target_minor": request.net_personal_target_minor, "required_gross_personal_minor": gross,
        "required_distributable_profit_minor": required_profit,
        "fixture_distributable_gap_minor": max(0, required_profit - eligible) if required_profit is not None else None,
        "options": options, "verified_after_tax_income_minor": None, "verified_commercial_revenue_minor": None,
        "requires_independent_review": True, "external_action_authorized": False,
    }
    return {**result, "sha256": artifact_digest("commercial_target_scenario", baseline["sha256"],
                                                {"inputs": request.model_dump(mode="json"), "result": result})}
