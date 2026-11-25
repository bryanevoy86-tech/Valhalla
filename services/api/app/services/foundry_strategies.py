"""Comparable, advisory-only business entry scenarios with disposable workforce evidence."""
from datetime import date
from typing import Annotated, Literal

from pydantic import Field, model_validator
from sqlalchemy import inspect

from app.models.go_live_state import GoLiveState
from app.schemas.market_intelligence import StrictModel
from app.services.foundry_discovery import AcquisitionTerms, Cents

Strategy = Literal["BUILD", "BUY", "PARTNER", "EXPAND"]
Role = Literal["INSTALLER", "FOREMAN", "PROPERTY_MANAGER", "SERVICE_OPERATOR", "LOCAL_OPERATOR", "LICENSED_PROFESSIONAL"]
Count = Annotated[int, Field(strict=True, ge=0, le=50)]
Bps = Annotated[int, Field(strict=True, ge=0, le=10_000)]
SourceId = Annotated[str, Field(min_length=3, max_length=80)]
STRATEGIES = ("BUILD", "BUY", "PARTNER", "EXPAND")


def rehearsal_allowed(db):
    from app.routers.foundry_operating_rehearsal import enabled
    from app.services.prime_business_execution import _emergency_stop_active

    if (not enabled() or not inspect(db.connection()).has_table(GoLiveState.__tablename__)
            or _emergency_stop_active(db)):
        return False
    release = db.get(GoLiveState, 1, populate_existing=True)
    return release is None or not release.go_live_enabled


class WorkforceCandidate(StrictModel):
    candidate_id: str = Field(pattern=r"^fixture:[a-z0-9-]{3,64}$")
    role: Role
    jurisdiction: str = Field(min_length=2, max_length=80)
    claims_experience: bool = False
    reference_source: SourceId | None = None
    practical_source: SourceId | None = None
    human_review_source: SourceId | None = None
    license_source: SourceId | None = None
    available_source: SourceId | None = None
    monthly_compensation: Cents
    retention_risk: Literal["LOW", "HIGH", "UNKNOWN"]

    @model_validator(mode="after")
    def distinct_checks(self):
        references = [ref for ref in (self.reference_source, self.practical_source, self.human_review_source,
                                     self.license_source, self.available_source) if ref]
        if len(references) != len(set(references)):
            raise ValueError("Qualification stages need distinct attributed checks")
        return self

    def qualification(self, jurisdiction):
        if jurisdiction != self.jurisdiction:
            return "WRONG_JURISDICTION"
        if not self.reference_source:
            return "CLAIMED_EXPERIENCE" if self.claims_experience else "UNVERIFIED"
        if not self.practical_source:
            return "REFERENCE_OR_CREDENTIAL_CHECKED"
        if not self.human_review_source or (self.role == "LICENSED_PROFESSIONAL" and not self.license_source):
            return "PRACTICAL_ASSESSMENT_RECORDED"
        if not self.available_source or self.retention_risk != "LOW":
            return "QUALIFIED_BUT_UNAVAILABLE"
        return "QUALIFIED_AND_AVAILABLE_IN_FIXTURE"


class PartnerTerms(StrictModel):
    revenue_share_bp: Bps
    guaranteed_monthly_compensation: Cents
    control: Literal["DEFINED_IN_FIXTURE", "UNRESOLVED"]


class StrategyCase(StrictModel):
    kind: Strategy
    setup_cost: Cents
    working_capital: Cents
    runway_months: Annotated[int, Field(strict=True, ge=1, le=24)]
    monthly_receipts: Cents
    monthly_cost_before_staff: Cents
    customer_concentration_bp: Bps
    recurring_receipts_bp: Bps
    owner_dependence_bp: Bps
    downside_receipt_reduction_bp: Bps
    downside_additional_cost: Cents
    demand_source: SourceId | None = None
    transfer_source: SourceId | None = None
    valuation_source: SourceId | None = None
    valuation_ceiling_minor: Cents | None = None
    control_source: SourceId | None = None
    unresolved_requirements: list[Annotated[str, Field(min_length=5, max_length=160)]] = Field(max_length=12)
    required_roles: dict[Role, Count] = Field(min_length=1, max_length=6)
    candidate_ids: list[str] = Field(max_length=50)
    acquisition: AcquisitionTerms | None = None
    partner: PartnerTerms | None = None

    @model_validator(mode="after")
    def valid_terms(self):
        if (self.kind == "BUY") != (self.acquisition is not None) or (self.kind == "PARTNER") != (self.partner is not None):
            raise ValueError("Acquisition and partner terms must match the strategy")
        if not all(self.required_roles.values()) or len(set(self.candidate_ids)) != len(self.candidate_ids):
            raise ValueError("Require positive coverage and count each candidate at most once")
        return self


class StrategyStudy(StrictModel):
    basis: Literal["DISPOSABLE_STRATEGY_FIXTURE"]
    cases: list[StrategyCase] = Field(min_length=4, max_length=4)
    candidates: list[WorkforceCandidate] = Field(max_length=50)
    cash_ceiling_cad_cents: Cents
    capital_hurdle_bp: Bps

    @model_validator(mode="after")
    def distinct_inputs(self):
        ids = {candidate.candidate_id for candidate in self.candidates}
        if len(ids) != len(self.candidates) or {case.kind for case in self.cases} != set(STRATEGIES):
            raise ValueError("Provide four distinct strategies and distinct fixture candidates")
        if any(set(case.candidate_ids) - ids for case in self.cases):
            raise ValueError("Strategies can reference only candidates in this scoped study")
        return self

    def source_requirements(self):
        requirements = {}
        for candidate in self.candidates:
            for key, value in candidate.model_dump().items():
                if key.endswith("_source") and value:
                    requirements.setdefault(value, set()).add(
                        f"{candidate.candidate_id}/{candidate.role}/{candidate.jurisdiction}/{key.removesuffix('_source')}"
                    )
        for case in self.cases:
            for key, value in case.model_dump().items():
                if key.endswith("_source") and value:
                    requirements.setdefault(value, set()).add(f"{case.kind}/{key.removesuffix('_source')}")
        return requirements


def evidence_matches(study, findings):
    available = {}
    for finding in findings:
        if finding["citation"].startswith("https://fixtures.example.invalid/"):
            available.setdefault(finding["source_id"], set()).update(finding.get("fixture_bindings", ()))
    return all(required <= available.get(source, set()) for source, required in study.source_requirements().items())


def project(study, jurisdiction, *, available=None, international=None, learning=None):
    cash = study.cash_ceiling_cad_cents if available is None else min(available, study.cash_ceiling_cad_cents)
    candidates = {item.candidate_id: item for item in study.candidates}
    qualifications = {key: item.qualification(jurisdiction) for key, item in candidates.items()}
    rows = []
    for case in study.cases:
        selected = [candidates[key] for key in case.candidate_ids
                    if qualifications[key] == "QUALIFIED_AND_AVAILABLE_IN_FIXTURE"]
        required = dict(case.required_roles)
        if international and international["inputs"]["local_operator_required"]:
            role = "PROPERTY_MANAGER" if international["inputs"]["kind"] == "REAL_ESTATE" else "LOCAL_OPERATOR"
            required[role] = max(required.get(role, 0), 1)
        gaps = {role: count - sum(item.role == role for item in selected)
                for role, count in required.items() if count > sum(item.role == role for item in selected)}
        staff_cost = sum(item.monthly_compensation for item in selected)
        debt = case.acquisition.monthly_debt_service if case.acquisition else 0
        fixed = case.monthly_cost_before_staff + staff_cost + debt
        if case.partner:
            fixed += case.partner.guaranteed_monthly_compensation
        share = case.partner.revenue_share_bp if case.partner else 0
        shock = max(case.downside_receipt_reduction_bp, case.customer_concentration_bp,
                    case.owner_dependence_bp if case.kind == "BUY" else 0)
        stress_receipts = case.monthly_receipts * (10_000 - shock) // 10_000
        net = case.monthly_receipts * (10_000 - share) // 10_000 - fixed
        stress = stress_receipts * (10_000 - share) // 10_000 - fixed - case.downside_additional_cost
        upfront = case.setup_cost + case.working_capital + case.runway_months * (fixed + case.downside_additional_cost)
        if case.acquisition:
            upfront += case.acquisition.required_equity
        if international:
            # A common local stress floor may further constrain a CAD strategy estimate.
            upfront = max(upfront, international["stress"]["required_cash_cad_cents"])
            stress = min(stress, international["stress"]["monthly_net_cad_cents"])
        opportunity_cost = upfront * study.capital_hurdle_bp // 10_000
        conservative_value = 12 * stress - opportunity_cost
        blockers = [reason for active, reason in (
            (not case.demand_source, "DEMAND_UNCORROBORATED"),
            (bool(gaps), "QUALIFIED_COVERAGE_MISSING"),
            (upfront > cash, "INSUFFICIENT_CASH_AND_RUNWAY"),
            (stress <= 0 or conservative_value <= 0, "DOWNSIDE_OR_CAPITAL_COST_UNACCEPTABLE"),
            (bool(case.unresolved_requirements), "DILIGENCE_UNRESOLVED"),
            (case.kind == "BUY" and (not case.transfer_source or case.owner_dependence_bp > 5000),
             "CUSTOMER_OR_OWNER_TRANSFER_UNSUPPORTED"),
            (case.kind == "BUY" and (not case.valuation_source or not case.valuation_ceiling_minor),
             "ACQUISITION_VALUATION_UNCORROBORATED"),
            (case.acquisition is not None and case.valuation_ceiling_minor is not None
             and case.acquisition.purchase_price > case.valuation_ceiling_minor, "PURCHASE_PRICE_EXCEEDS_VALUATION"),
            (case.partner is not None and (case.partner.control != "DEFINED_IN_FIXTURE" or not case.control_source),
             "PARTNER_CONTROL_UNRESOLVED"),
            (bool(learning and case.kind in {"BUY", "EXPAND"}), "SCOPED_OPERATING_LOSS_REQUIRES_REESTIMATE"),
        ) if active]
        if international:
            blockers.extend(international["blockers"])
        rows.append({
            "strategy": case.kind, "required_cash_minor": upfront, "monthly_contribution_minor": net,
            "runway_months": case.runway_months, "working_capital_minor": case.working_capital,
            "purchase_price_minor": case.acquisition.purchase_price if case.acquisition else None,
            "financed_principal_minor": case.acquisition.financed_principal if case.acquisition else 0,
            "valuation_ceiling_minor": case.valuation_ceiling_minor,
            "monthly_debt_service_minor": debt, "partner_revenue_share_bp": share,
            "customer_concentration_bp": case.customer_concentration_bp, "owner_dependence_bp": case.owner_dependence_bp,
            "downside_basis": "LARGEST_SINGLE_RECEIPTS_SHOCK_PLUS_ADDITIONAL_COSTS",
            "stressed_monthly_contribution_minor": stress, "downside_receipt_reduction_bp": shock,
            "recurring_receipts_bp": case.recurring_receipts_bp, "monthly_staff_cost_minor": staff_cost,
            "annual_opportunity_cost_minor": opportunity_cost, "conservative_annual_value_minor": conservative_value,
            "coverage_gaps": gaps, "blockers": blockers, "eligible_internal_proposal": not blockers,
        })
    rows.sort(key=lambda row: (not row["eligible_internal_proposal"], -row["conservative_annual_value_minor"],
                               row["required_cash_minor"], row["strategy"]))
    preferred = next((row["strategy"] for row in rows if row["eligible_internal_proposal"]), "HOLD")
    return {"basis": study.basis, "currency": "CAD", "available_cash_minor": cash,
            "funding_basis": "DECLARED_STUDY_CEILING" if available is None else "SCOPED_RECONCILIATION_FIXTURE",
            "qualifications": qualifications, "alternatives": rows, "preferred_internal_proposal": preferred,
            "selection_basis": "BEST_SUPPORTED_STRESSED_VALUE_AFTER_CAPITAL_COST" if preferred != "HOLD" else "NO_SUPPORTED_ENTRY",
            "learning_sha256": learning, "professional_and_owner_approval_required": True,
            "verified_commercial_evidence": False, "external_authority": False}
