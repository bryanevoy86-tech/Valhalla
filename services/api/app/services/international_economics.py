"""Cross-border scenarios expressed in local minor units and CAD cents."""
from datetime import date
from typing import Annotated, Literal

from pydantic import Field, model_validator

from app.schemas.market_intelligence import StrictModel


Money = Annotated[int, Field(strict=True, ge=0, le=10_000_000_000)]
Bps = Annotated[int, Field(strict=True, ge=0, le=10_000)]
Topic = Literal["OWNERSHIP", "REGISTRATION", "LABOUR", "TAX", "LICENSING",
                "CROSS_BORDER_TRANSFERS", "FINANCING", "PROPERTY_USE"]
COMMON_TOPICS = {"OWNERSHIP", "REGISTRATION", "LABOUR", "TAX", "LICENSING",
                 "CROSS_BORDER_TRANSFERS", "FINANCING"}


class ProfessionalQuestion(StrictModel):
    topic: Topic
    question: str = Field(min_length=12, max_length=300)
    status: Literal["UNRESOLVED", "ASSUMPTION_ONLY"]


class InternationalStudy(StrictModel):
    kind: Literal["SERVICE", "REAL_ESTATE"]
    country: str = Field(pattern=r"^[A-Z]{2}$")
    region: str = Field(pattern=r"^[A-Z0-9]{1,6}$")
    local_currency: str = Field(pattern=r"^[A-Z]{3}$")
    # Ratio explicitly includes the relative minor-unit scales of the currencies.
    cad_cents_per_local_minor_ppm: Annotated[int, Field(strict=True, gt=0, le=1_000_000_000)]
    fx_source_id: str = Field(min_length=3, max_length=80)
    fx_observed_on: date
    fx_stress_bps: Annotated[int, Field(strict=True, gt=0, lt=10_000)]
    conversion_fee_bps: Annotated[int, Field(strict=True, ge=0, lt=10_000)]
    monthly_revenue_local_minor: Money
    revenue_stress_bps: Bps
    labour_local_minor: Money
    property_management_local_minor: Money
    local_operator_local_minor: Money
    other_monthly_expenses_local_minor: Money
    tax_reserve_local_minor: Money
    debt_service_local_minor: Money
    acquisition_and_setup_local_minor: Money
    financing_principal_local_minor: Money
    working_capital_local_minor: Money
    cross_border_setup_cad_cents: Money
    local_operator_required: bool = Field(strict=True)
    local_operator_status: Literal["UNIDENTIFIED", "HYPOTHETICAL", "NOT_REQUIRED"]
    professional_questions: list[ProfessionalQuestion] = Field(min_length=7, max_length=8)

    @model_validator(mode="after")
    def validate_assumptions(self):
        required = COMMON_TOPICS | ({"PROPERTY_USE"} if self.kind == "REAL_ESTATE" else set())
        topics = [item.topic for item in self.professional_questions]
        if len(topics) != len(set(topics)) or not required <= set(topics):
            raise ValueError("List each required professional question once")
        if self.financing_principal_local_minor > self.acquisition_and_setup_local_minor:
            raise ValueError("Modeled financing cannot exceed acquisition and setup costs")
        if bool(self.financing_principal_local_minor) != bool(self.debt_service_local_minor):
            raise ValueError("Provide both financing principal and scheduled debt service")
        if self.local_operator_required != (self.local_operator_status != "NOT_REQUIRED"):
            raise ValueError("Local operator status must agree with the operating requirement")
        if self.local_operator_required and not (self.local_operator_local_minor or self.property_management_local_minor):
            raise ValueError("Include a cost assumption for the required local operator")
        if self.country == "CA" or self.local_currency == "CAD":
            raise ValueError("International scenarios require a foreign jurisdiction and local currency")
        return self


def project_international(study):
    rate = study.cad_cents_per_local_minor_ppm
    stress = study.fx_stress_bps
    fee = study.conversion_fee_bps
    operating_cost = (study.labour_local_minor + study.property_management_local_minor
                      + study.local_operator_local_minor + study.other_monthly_expenses_local_minor
                      + study.tax_reserve_local_minor + study.debt_service_local_minor)
    equity_and_working_cash = (study.acquisition_and_setup_local_minor - study.financing_principal_local_minor
                               + study.working_capital_local_minor)
    denominator = 1_000_000 * 10_000**2

    def scenario(revenue, stress_bps):
        # Buy local currency at the high side; value converted receipts at the low side.
        receipts = revenue * rate * (10_000 - stress_bps) * (10_000 - fee) // denominator
        purchase_factor = rate * (10_000 + stress_bps) * (10_000 + fee)
        costs = (operating_cost * purchase_factor + denominator - 1) // denominator
        upfront = (equity_and_working_cash * purchase_factor + denominator - 1) // denominator
        return {
            "monthly_receipts_cad_cents": receipts,
            "monthly_costs_cad_cents": costs,
            "monthly_net_cad_cents": receipts - costs,
            "required_cash_cad_cents": upfront + study.cross_border_setup_cad_cents,
        }

    base = scenario(study.monthly_revenue_local_minor, 0)
    stressed_revenue = study.monthly_revenue_local_minor * (10_000 - study.revenue_stress_bps) // 10_000
    downside = scenario(stressed_revenue, stress)
    blockers = ["INTERNATIONAL_PROFESSIONAL_DILIGENCE_UNRESOLVED"]
    if study.local_operator_required:
        blockers.append("LOCAL_OPERATOR_UNVERIFIED")
    if downside["monthly_net_cad_cents"] <= 0:
        blockers.append("INTERNATIONAL_STRESS_NONPOSITIVE")
    return {
        "basis": "CROSS_BORDER_SCENARIO_ONLY",
        "inputs": study.model_dump(mode="json"),
        "base": base,
        "stress": downside,
        "blockers": blockers,
        "decision": "HOLD_FOR_VERIFIED_EVIDENCE",
        "verified_commercial_revenue": False,
        "external_authority": False,
    }
