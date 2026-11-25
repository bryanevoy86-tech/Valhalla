"""Advisory skilled-trade planning with explicit crew and cash assumptions."""
from typing import Annotated, Literal

from pydantic import Field, model_validator

from app.schemas.market_intelligence import StrictModel


Money = Annotated[int, Field(strict=True, ge=0, le=100_000_000)]
PositiveMoney = Annotated[int, Field(strict=True, gt=0, le=100_000_000)]
Workers = Annotated[int, Field(strict=True, ge=0, le=100)]
CrewSize = Annotated[int, Field(strict=True, ge=1, le=20)]
Days = Annotated[int, Field(strict=True, ge=0, le=365)]
BasisPoints = Annotated[int, Field(strict=True, ge=0, le=10_000)]


class TradeScenario(StrictModel):
    name: Literal["BASE", "STRESS", "EXPANSION"]
    price_minor: PositiveMoney
    crew_count: Annotated[int, Field(strict=True, ge=1, le=5)]
    crew_size: CrewSize
    available_skilled_workers: Workers
    available_foremen: Workers
    hours_per_worker_week: Annotated[int, Field(strict=True, ge=5, le=60)]
    days_per_week: Annotated[int, Field(strict=True, ge=1, le=7)]
    wage_minor_per_hour: PositiveMoney
    employer_burden_bps: BasisPoints
    on_site_days: Annotated[int, Field(strict=True, ge=1, le=180)]
    weather_delay_days: Days
    mobilization_hours_per_crew: Annotated[int, Field(strict=True, ge=0, le=720)]
    seasonal_utilization_bps: BasisPoints
    estimated_demand_jobs_per_month: Annotated[int, Field(strict=True, ge=0, le=100)]
    materials_minor: Money
    job_equipment_travel_minor: Money
    callback_reserve_minor: Money
    monthly_overhead_minor: Money
    admin_mode: Literal["OWNER", "DELEGATED"]
    monthly_admin_hours: Annotated[int, Field(strict=True, ge=1, le=720)]
    admin_minor_per_hour: PositiveMoney
    setup_minor: Money
    payment_days_after_delivery: Days
    duration_basis: str = Field(min_length=12, max_length=240)

    @model_validator(mode="after")
    def validate_staffing(self):
        if self.available_foremen > self.available_skilled_workers:
            raise ValueError("Available foremen are included in available skilled workers")
        if self.days_per_week > self.hours_per_worker_week:
            raise ValueError("Workdays cannot exceed weekly worker hours")
        return self


class SkilledTradeStudy(StrictModel):
    observed_crew_size: CrewSize
    observed_on_site_days: Annotated[int, Field(strict=True, ge=1, le=180)]
    scenarios: list[TradeScenario] = Field(min_length=3, max_length=3)

    @model_validator(mode="after")
    def validate_scenarios(self):
        cases = {case.name: case for case in self.scenarios}
        if set(cases) != {"BASE", "STRESS", "EXPANSION"}:
            raise ValueError("Provide baseline, downside and expansion alternatives")
        if cases["STRESS"].crew_count != cases["BASE"].crew_count:
            raise ValueError("Keep crew count fixed for the downside comparison")
        if cases["EXPANSION"].crew_count <= cases["BASE"].crew_count:
            raise ValueError("Expansion needs an additional crew")
        for case in self.scenarios:
            if case.crew_size < self.observed_crew_size and case.on_site_days <= self.observed_on_site_days:
                raise ValueError("A smaller crew needs a distinct, slower production assumption")
        return self


def _ceil(numerator, denominator):
    return -(-numerator // denominator)


def project_scenario(case):
    workers = case.crew_size * case.crew_count
    # Round time up at the job boundary. Average monthly hours use 52 weeks / 12.
    onsite_hours = _ceil(case.on_site_days * case.hours_per_worker_week, case.days_per_week)
    occupied_hours = onsite_hours + case.mobilization_hours_per_crew + _ceil(
        case.weather_delay_days * case.hours_per_worker_week, case.days_per_week
    )
    paid_job_hours = (onsite_hours + case.mobilization_hours_per_crew) * case.crew_size
    capacity = (
        52 * case.hours_per_worker_week * case.crew_count * case.seasonal_utilization_bps
        // (12 * 10_000 * occupied_hours)
    )
    jobs = min(capacity, case.estimated_demand_jobs_per_month)
    loaded_rate = _ceil(case.wage_minor_per_hour * (10_000 + case.employer_burden_bps), 10_000)
    monthly_payroll = _ceil(52 * case.hours_per_worker_week * workers * loaded_rate, 12)
    non_labor_per_job = case.materials_minor + case.job_equipment_travel_minor + case.callback_reserve_minor
    admin_cost = case.monthly_admin_hours * case.admin_minor_per_hour
    admin_cash_cost = admin_cost if case.admin_mode == "DELEGATED" else 0
    revenue = jobs * case.price_minor
    recurring_cost = monthly_payroll + jobs * non_labor_per_job + case.monthly_overhead_minor
    contribution = revenue - recurring_cost - admin_cost
    cash_outflow = recurring_cost + admin_cash_cost
    job_cycle_days = _ceil(7 * occupied_hours, case.hours_per_worker_week)
    collection_cycle_days = job_cycle_days + case.payment_days_after_delivery
    worker_gap = max(0, workers - case.available_skilled_workers)
    foreman_gap = max(0, case.crew_count - case.available_foremen)
    return {
        "name": case.name, "paid_worker_hours_per_job": paid_job_hours,
        "occupied_crew_hours_per_job": occupied_hours, "loaded_wage_minor_per_hour": loaded_rate,
        "estimated_job_direct_cost_minor": paid_job_hours * loaded_rate + non_labor_per_job,
        "capacity_jobs_per_month": capacity, "modeled_jobs_per_month": jobs,
        "monthly_payroll_minor": monthly_payroll, "monthly_admin_cost_minor": admin_cost,
        "monthly_cash_outflow_minor": cash_outflow, "projected_monthly_revenue_minor": revenue,
        "monthly_operating_contribution_minor": contribution,
        "receivables_proxy_minor": _ceil(revenue * case.payment_days_after_delivery, 30),
        "collection_cycle_days": collection_cycle_days,
        "startup_cash_reserve_proxy_minor": case.setup_minor + _ceil(cash_outflow * collection_cycle_days, 30),
        "workers_required": workers, "foremen_required": case.crew_count,
        "skilled_worker_gap": worker_gap, "foreman_gap": foreman_gap,
        "owner_admin_hours_per_month": case.monthly_admin_hours if case.admin_mode == "OWNER" else 0,
        "blockers": [reason for active, reason in (
            (worker_gap, "SKILLED_WORKERS_UNAVAILABLE"), (foreman_gap, "FOREMAN_UNAVAILABLE"),
            (contribution <= 0, "NONPOSITIVE_CONTRIBUTION"), (jobs == 0, "NO_MODELED_THROUGHPUT"),
        ) if active],
    }


def project_trade(study):
    results = {case.name: project_scenario(case) for case in study.scenarios}
    base, stress, expansion = (results[name] for name in ("BASE", "STRESS", "EXPANSION"))
    expansion_blockers = list(expansion["blockers"])
    if base["blockers"] or stress["blockers"]:
        expansion_blockers.append("BASE_OR_DOWNSIDE_UNVIABLE")
    if expansion["monthly_operating_contribution_minor"] <= base["monthly_operating_contribution_minor"]:
        expansion_blockers.append("NO_INCREMENTAL_CONTRIBUTION")
    return {
        "basis": "ATTRIBUTED_OBSERVATION_AND_DECLARED_SCENARIOS",
        "inputs": study.model_dump(mode="json"), "scenarios": results,
        "expansion_blockers": expansion_blockers, "decision": "HOLD_FOR_VERIFIED_EVIDENCE",
        "verified_commercial_revenue": False, "external_authority": False,
    }
