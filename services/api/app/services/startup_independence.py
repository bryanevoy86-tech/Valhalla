"""Private startup planning over explicitly classified rehearsal evidence."""
from datetime import date, timedelta
from typing import Annotated, Literal

from pydantic import Field, model_validator

from app.schemas.market_intelligence import StrictModel

Minor = Annotated[int, Field(strict=True, ge=0, le=100_000_000_000)]
Reference = Annotated[str, Field(min_length=3, max_length=120)]
ReviewDay = Literal[15, 30, 45, 60, 75, 90]
Category = Literal[
    "SETTLED_BUSINESS_REVENUE", "BUSINESS_EXPENSE", "BUSINESS_ASSET", "OWNER_CONTRIBUTION",
    "PERSONAL_ASSET_SALE", "RETAINED_EARNINGS", "GROSS_PERSONAL_COMPENSATION", "PERSONAL_TAX",
    "GRANT", "LOAN", "SUBSIDY", "TECHNOLOGY_CREDIT", "CUSTOMER_ADVANCE", "REFUND", "ASSISTANCE",
]

REVIEW_FOCUS = {
    15: "DEMAND_PROSPECTS_AND_PILOT_READINESS",
    30: "SETTLED_REVENUE_AND_BOTTLENECKS",
    45: "REPEATABLE_ACQUISITION_AND_PROFITABILITY",
    60: "HOUSEHOLD_INCOME_SUSTAINABILITY",
    75: "RESERVES_AND_PROFITABLE_EXPANSION",
    90: "FINANCIAL_INDEPENDENCE_STRETCH_REVIEW",
}


class ReportingLine(StrictModel):
    category: Category
    amount_minor: Minor
    occurred_on: date
    evidence_ref: Reference
    basis: Literal["SYNTHETIC_FIXTURE", "OWNER_REPORTED"]


class FundingLine(StrictModel):
    evidence_ref: Reference
    kind: Literal["GRANT", "REIMBURSEMENT", "CREDIT", "LOAN", "CUSTOMER_ADVANCE", "OWNER_CONTRIBUTION"]
    status: Literal["DISCOVERED", "POTENTIALLY_ELIGIBLE", "VERIFIED_ELIGIBLE", "APPLICATION_PREPARED",
                    "SUBMITTED", "APPROVED", "RECEIVED", "RESTRICTED", "REIMBURSABLE", "CLOSED"]
    amount_minor: Minor


class StartupIndependenceIn(StrictModel):
    registration_date: date | None = None
    registration_evidence_ref: Reference | None = None
    commissioning_date: date | None = None
    monthly_essentials_minor: Minor
    reserve_months: int = Field(strict=True, ge=1, le=24)
    reserve_balance_minor: Minor
    monthly_stretch_low_minor: Minor
    monthly_stretch_high_minor: Minor
    completed_reviews: list[ReviewDay] = Field(default_factory=list, max_length=6)
    opening_unrestricted_cash_fixture_minor: Minor
    establishment_minor: Minor
    operating_minor: Minor
    business_reserve_minor: Minor
    experiment_minor: Minor
    hypothetical_extra_contributions_minor: list[Minor] = Field(default_factory=list, max_length=12)
    funding: list[FundingLine] = Field(default_factory=list, max_length=50)
    reporting_month: date
    reporting_lines: list[ReportingLine] = Field(default_factory=list, max_length=100)
    reporting_rules_ref: Reference | None = None
    reporting_rules_checked_on: date | None = None
    case_confirmation_ref: Reference | None = None

    @model_validator(mode="after")
    def validate_report(self):
        if bool(self.registration_date) != bool(self.registration_evidence_ref):
            raise ValueError("Registration requires a date and private evidence reference")
        if self.commissioning_date is not None and (
            self.registration_date is None or self.commissioning_date < self.registration_date
        ):
            raise ValueError("Commissioning must follow recorded registration")
        if (self.reporting_month.day != 1 or self.monthly_stretch_low_minor > self.monthly_stretch_high_minor
                or bool(self.reporting_rules_ref) != bool(self.reporting_rules_checked_on)):
            raise ValueError("Invalid reporting month, stretch range or dated rules reference")
        if len(set(self.completed_reviews)) != len(self.completed_reviews):
            raise ValueError("Review days must be distinct")
        for records in (self.reporting_lines, self.funding):
            refs = [item.evidence_ref.casefold() for item in records]
            if len(set(refs)) != len(refs):
                raise ValueError("Evidence references must be unique within each group")
        if any(item.occurred_on.replace(day=1) != self.reporting_month for item in self.reporting_lines):
            raise ValueError("Reporting records must belong to the selected month")
        return self


def startup_independence(plan: StartupIndependenceIn, today: date) -> dict:
    from fastapi import HTTPException

    registered = plan.registration_date
    if ((registered and registered > today) or (plan.commissioning_date and plan.commissioning_date > today)
            or (not registered and plan.completed_reviews)
            or any(registered + timedelta(days=day) > today for day in plan.completed_reviews)
            or plan.reporting_month > today or any(item.occurred_on > today for item in plan.reporting_lines)
            or (plan.reporting_rules_checked_on and plan.reporting_rules_checked_on > today)):
        raise HTTPException(422, "Dates must describe evidence already available")
    milestones = []
    if registered:
        for day, focus in REVIEW_FOCUS.items():
            due = registered + timedelta(days=day)
            status = ("OWNER_REPORTED_COMPLETE" if day in plan.completed_reviews else
                      "REASSESS" if due <= today else "UPCOMING")
            milestones.append({"day": day, "due": due.isoformat(), "focus": focus, "status": status})

    protected = plan.establishment_minor + plan.operating_minor + plan.business_reserve_minor
    required = protected + plan.experiment_minor
    capital = []
    for contribution in sorted({0, *plan.hypothetical_extra_contributions_minor}):
        cash = plan.opening_unrestricted_cash_fixture_minor + contribution
        capital.append({
            "hypothetical_extra_contribution_minor": contribution, "cash_fixture_minor": cash,
            "minimum_establishment_gap_minor": max(0, plan.establishment_minor - cash),
            "protected_capital_gap_minor": max(0, protected - cash),
            "experiment_headroom_minor": max(0, cash - protected),
            "total_plan_gap_minor": max(0, required - cash),
        })

    totals = {}
    for line in plan.reporting_lines:
        row = totals.setdefault(line.category, {})
        row[line.basis] = row.get(line.basis, 0) + line.amount_minor
    # Incomplete tax or pay evidence carries no net-income inference.
    reported = "OWNER_REPORTED"
    gross = totals.get("GROSS_PERSONAL_COMPENSATION", {}).get(reported)
    tax = totals.get("PERSONAL_TAX", {}).get(reported)
    net = gross - tax if gross is not None and tax is not None else None
    assistance = totals.get("ASSISTANCE", {}).get(reported)
    shortfall = max(0, plan.monthly_essentials_minor - net - assistance) if net is not None and assistance is not None else None
    reserve_target = plan.monthly_essentials_minor * plan.reserve_months
    return {
        "currency": "CAD", "basis": "PRIVATE_STARTUP_PLANNING", "registration_date": registered,
        "commissioning_date": plan.commissioning_date, "reviews": milestones,
        "reassessment_required": any(review["status"] == "REASSESS" for review in milestones),
        "capital_scenarios": capital, "verified_available_cash_minor": None,
        "funding": [{**line.model_dump(), "included_in_spendable_cash_minor": 0,
                     "requires_settlement_and_use_review": True} for line in plan.funding],
        "monthly_essentials_minor": plan.monthly_essentials_minor,
        "personal_reserve_target_minor": reserve_target,
        "personal_reserve_gap_minor": max(0, reserve_target - plan.reserve_balance_minor),
        "stretch_net_monthly_minor": [plan.monthly_stretch_low_minor, plan.monthly_stretch_high_minor],
        "stretch_guaranteed": False, "owner_reported_gross_compensation_minor": gross,
        "owner_reported_tax_minor": tax, "owner_estimated_net_income_minor": net,
        "verified_after_tax_income_minor": None, "household_estimated_shortfall_minor": shortfall,
        "support_forecast_minor": None,
        "reporting": {
            "month": plan.reporting_month, "status": "DRAFT_REQUIRES_OFFICIAL_AND_CASE_REVIEW",
            "owner_rules_reference_supplied": plan.reporting_rules_ref is not None,
            "owner_case_reference_supplied": plan.case_confirmation_ref is not None,
            "official_or_case_evidence_verified": False,
            "totals_by_category_and_basis": totals,
            "lines": [line.model_dump(mode="json") for line in plan.reporting_lines],
            "checklist": ["GATHER_REGISTRATION_RECORD", "CONFIRM_NOTICE_AND_REPORTING_DEADLINES",
                          "CLASSIFY_AND_RECONCILE_ALL_INCOME_ASSETS_FUNDING_AND_EXPENSES",
                          "CONFIRM_RETAINED_EARNINGS_AND_ASSISTANCE_TREATMENT",
                          "REVIEW_WITH_PROGRAM_CONTACT_BEFORE_SUBMISSION"],
        },
        "external_action_authorized": False, "borrowing_authorized": False,
        "transfers_authorized": False, "contingency_activation_authorized": False,
    }
