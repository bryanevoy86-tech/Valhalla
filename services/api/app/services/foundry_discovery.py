"""Evaluate scoped, rights-attested source records without performing commerce."""
from datetime import date, timedelta
from typing import Annotated, Literal
from uuid import UUID

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import inspect, select
from sqlalchemy.orm import Session

from app.loki.evidence import artifact_digest
from app.models.foundry_evidence import FoundryEvidence
from app.services.specialist_triggers import outcome_scope_key


Cents = Annotated[int, Field(strict=True, ge=0, le=10_000_000_000)]
SCOPE_FIELDS = {"legacy_instance_id", "business_id", "engine_id", "jurisdiction"}
DISCOVERY_ROLES = frozenset({
    "ODIN", "HUGINN", "NJORD", "FREYJA", "TYR", "FORSETI", "NORNS", "HEIMDALL", "MIMIR", "LOKI", "BRAGI",
})


class AcquisitionTerms(BaseModel):
    model_config = ConfigDict(extra="forbid")
    purchase_price: Cents
    closing_and_transition_cost: Cents
    funded_working_reserve: Cents
    financed_principal: Cents
    monthly_debt_service: Cents

    @model_validator(mode="after")
    def validate_funding(self):
        if self.purchase_price == 0 or self.financed_principal > self.purchase_price:
            raise ValueError("Acquisition financing must be covered by a positive purchase price")
        if bool(self.financed_principal) != bool(self.monthly_debt_service):
            raise ValueError("Declare debt service only for financed acquisitions")
        return self

    @property
    def required_equity(self):
        return self.purchase_price - self.financed_principal + self.closing_and_transition_cost + self.funded_working_reserve


class DiscoveryProvenance(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_id: str
    adapter: Literal["DEMAND_EXPORT", "PROCUREMENT_EXPORT"]
    citation: str
    external_key: str
    job_sha256: str
    sample_count: int
    demand_count: int
    buyer_segment: str


class EvidenceIn(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    evidence_id: UUID
    legacy_instance_id: str = Field(min_length=3, max_length=80)
    business_id: str = Field(min_length=3, max_length=120)
    engine_id: str = Field(min_length=3, max_length=80)
    jurisdiction: str = Field(min_length=2, max_length=80)
    kind: Literal["ACQUISITION", "DIGITAL_PRODUCT", "SAAS", "SERVICE", "REAL_ESTATE", "OTHER"]
    evidence_class: Literal["OPERATOR_REPORTED", "SIMULATION"]
    title: str = Field(min_length=3, max_length=180)
    source_ref: str = Field(min_length=3, max_length=240)
    observed_on: date
    expires_on: date
    currency: Literal["CAD", "USD", "GBP", "EUR"]
    unit_price: Cents
    variable_cost_per_unit: Cents
    acquisition_cost_per_unit: Cents
    monthly_fixed_cost: Cents
    startup_capital: Cents
    test_cost: Cents
    monthly_units: int = Field(strict=True, ge=0, le=1_000_000)
    rights_attestation: Literal["AUTHORIZED_INTERNAL_RESEARCH"]
    acquisition: AcquisitionTerms | None = None
    revenue_model: Literal["ONE_TIME", "RECURRING", "ASSET", "SERVICE", "SUBSCRIPTION", "ACQUISITION", "OTHER"] | None = None
    provenance: DiscoveryProvenance | None = None

    @model_validator(mode="after")
    def validate_dates(self):
        if not self.observed_on <= self.expires_on <= self.observed_on + timedelta(days=366):
            raise ValueError("Invalid evidence validity dates")
        if self.acquisition and (self.kind != "ACQUISITION" or self.startup_capital < self.acquisition.required_equity):
            raise ValueError("Acquisition scenario requires acquisition evidence and adequate declared startup capital")
        return self


def economics(payload: EvidenceIn) -> dict:
    contribution = payload.unit_price - payload.variable_cost_per_unit - payload.acquisition_cost_per_unit
    estimated = contribution * payload.monthly_units - payload.monthly_fixed_cost
    stressed_units = payload.monthly_units * 3 // 4
    result = {
        "basis": "DECLARED_INPUTS_ONLY", "currency": payload.currency,
        "monthly_units": payload.monthly_units, "unit_contribution_minor": contribution,
        "break_even_units": ((payload.monthly_fixed_cost + contribution - 1) // contribution if contribution > 0 else None),
        "estimated_monthly_operating_contribution_minor": estimated,
        "stress_monthly_units": stressed_units,
        "stress_monthly_operating_contribution_minor": contribution * stressed_units - payload.monthly_fixed_cost,
        "declared_startup_capital_minor": payload.startup_capital, "declared_validation_cost_minor": payload.test_cost,
        "verified_revenue_minor": None,
    }
    if payload.acquisition:
        terms = payload.acquisition
        debt = terms.monthly_debt_service
        stress = result["stress_monthly_operating_contribution_minor"]
        result["acquisition"] = {
            "declared_purchase_price_minor": terms.purchase_price,
            "declared_financed_principal_minor": terms.financed_principal,
            "required_equity_and_reserve_minor": terms.required_equity,
            "monthly_debt_service_minor": debt,
            "monthly_available_cash_after_debt_minor": estimated - debt,
            "stress_monthly_available_cash_after_debt_minor": stress - debt,
            "operating_cash_to_debt_service_bp": 10000 * estimated // debt if debt else None,
            "stress_operating_cash_to_debt_service_bp": 10000 * stress // debt if debt else None,
            "debt_inclusive_break_even_units": ((payload.monthly_fixed_cost + debt + contribution - 1) // contribution
                                               if contribution > 0 else None),
            "financing_verified": False,
        }
    return result


def economic_blockers(kind: str, measures: dict) -> list[str]:
    """Use the same declared-economics constraints in advisory and simulated allocation."""
    blockers = []
    acquisition = measures.get("acquisition")
    if kind == "ACQUISITION" and not acquisition:
        blockers.append("ACQUISITION_TERMS_MISSING")
    if acquisition and acquisition["stress_monthly_available_cash_after_debt_minor"] < 0:
        blockers.append("ACQUISITION_DEBT_STRESS_SHORTFALL")
    if measures["stress_monthly_operating_contribution_minor"] < 0:
        blockers.append("STRESSED_OPERATING_CONTRIBUTION_NEGATIVE")
    return blockers


WITHDRAWAL_PREFIX = "WITHDRAWN-"


def withdrawal_trigger(row: FoundryEvidence) -> str:
    return f"{WITHDRAWAL_PREFIX}{row.id}-{row.digest[:24]}"


def verify_withdrawal(db: Session, scope: dict, event: str) -> bool:
    if not event.startswith(WITHDRAWAL_PREFIX) or not inspect(db.connection()).has_table(FoundryEvidence.__tablename__):
        return False
    try:
        evidence_id = UUID(event.removeprefix(WITHDRAWAL_PREFIX).rsplit("-", 1)[0])
    except ValueError:
        return False
    row = db.get(FoundryEvidence, evidence_id)
    return bool(
        row is not None and row.revoked and row.scope_key == outcome_scope_key(scope)
        and isinstance(row.payload, dict)
        and all(row.payload.get(key) == scope.get(key) for key in SCOPE_FIELDS)
        and row.digest == artifact_digest("foundry_evidence", str(row.id), row.payload)
        and event == withdrawal_trigger(row)
    )


def checked_evidence(row: FoundryEvidence, scope: dict, today: date, *, db=None) -> EvidenceIn:
    if (row.scope_key != outcome_scope_key(scope) or row.revoked
            or not row.observed_on <= today <= row.expires_on
            or row.digest != artifact_digest("foundry_evidence", str(row.id), row.payload)):
        raise HTTPException(409, "Foundry evidence is stale, revised or outside scope")
    payload = EvidenceIn.model_validate(row.payload)
    if (payload.model_dump(include=SCOPE_FIELDS) != scope or payload.observed_on != row.observed_on
            or payload.expires_on != row.expires_on or payload.source_ref != row.source_ref):
        raise HTTPException(409, "Foundry evidence metadata has changed")
    if payload.provenance:
        from app.services.foundry_intake import FoundryIntakeJob, Intake, intake_ready, source_for

        if db is None or not intake_ready(db):
            raise HTTPException(409, "Authorized discovery provenance unavailable")
        job = db.get(FoundryIntakeJob, row.id)
        if (job is None or job.status != "COMPLETED" or job.digest != payload.provenance.job_sha256
                or job.digest != artifact_digest("foundry_intake", str(job.id), job.payload)):
            raise HTTPException(409, "Discovery provenance failed integrity")
        source_for(db, Intake.model_validate(job.payload), today)
        superseding_id = db.scalar(select(FoundryEvidence.id).where(
            FoundryEvidence.scope_key == row.scope_key, FoundryEvidence.source_ref == row.source_ref,
            FoundryEvidence.observed_on > row.observed_on,
        ).limit(1))
        if superseding_id is not None:
            raise HTTPException(409, "A newer observation supersedes this source record")
    return payload


def demand_evidence(payload: EvidenceIn):
    item = payload.provenance
    if not item:
        return None
    return {**item.model_dump(), "sample_demand_bp": item.demand_count * 10000 // item.sample_count,
            "independently_validated": False}


def review_priority(role: str, metrics: dict) -> str:
    if role in {"TYR", "FORSETI", "HUGINN"}:
        return "VERIFY_SOURCE_AND_RIGHTS"
    if role == "NORNS":
        return "COMPARE_BASE_AND_STRESS_ASSUMPTIONS"
    if role == "MIMIR":
        return "PRESERVE_SOURCE_AND_COMPARE_OPERATING_OUTCOMES"
    if role == "LOKI":
        return "CHALLENGE_DEMAND_AND_COST_ASSUMPTIONS"
    if role == "FREYJA":
        return "VALIDATE_DEMAND_AND_ACQUISITION_COST"
    acquisition = metrics.get("acquisition")
    if acquisition and acquisition["stress_monthly_available_cash_after_debt_minor"] < 0:
        return "INVESTIGATE_ACQUISITION_DEBT_COVERAGE"
    contribution = metrics["estimated_monthly_operating_contribution_minor"]
    if metrics["unit_contribution_minor"] <= 0 or contribution < 0:
        return "INVESTIGATE_UNVIABLE_ECONOMICS"
    if metrics["stress_monthly_operating_contribution_minor"] < 0:
        return "INVESTIGATE_VOLUME_SENSITIVITY"
    return "VALIDATE_DECLARED_ECONOMICS"


def discover(db: Session, role: str, scope: dict, today: date) -> dict:
    from app.services.consumer_evidence import read_consumer_evidence

    if not inspect(db.connection()).has_table(FoundryEvidence.__tablename__):
        return {"foundry_signal_status": "SOURCE_SCHEMA_UNAVAILABLE", "foundry_signals": []}
    rows = db.scalars(select(FoundryEvidence).where(
        FoundryEvidence.scope_key == outcome_scope_key(scope),
        FoundryEvidence.revoked.is_(False),
        FoundryEvidence.observed_on <= today, FoundryEvidence.expires_on >= today,
    ).order_by(FoundryEvidence.observed_on.desc(), FoundryEvidence.id).limit(20)).all()
    signals = []
    rejected = []
    research_holds = []
    for row in rows:
        try:
            payload = checked_evidence(row, scope, today, db=db)
        except (HTTPException, ValueError):
            rejected.append(str(row.id))
            continue
        metrics = economics(payload)
        research = None
        try:
            research = read_consumer_evidence(db, row, payload, scope, today)
        except HTTPException:
            research_holds.append(str(row.id))
        signals.append({
            "evidence_id": str(row.id), "sha256": row.digest, "source_ref": row.source_ref,
            "title": payload.title, "kind": payload.kind, "evidence_class": payload.evidence_class,
            "priority": review_priority(role, metrics), "economics": metrics, "demand_evidence": demand_evidence(payload),
            **({"consumer_research": research} if research is not None else {}),
        })
    return {"foundry_signal_status": "OBSERVED" if signals else "NO_ELIGIBLE_SOURCE",
            "foundry_signals": signals, "invalid_foundry_evidence_ids": rejected,
            **({"consumer_research_holds": research_holds} if research_holds else {})}


def candidate_fields(row: FoundryEvidence, payload: EvidenceIn, report_id: str, *, consumer_research=None) -> dict:
    return {
        "opportunity_id": f"foundry-{row.id}",
        "source": "scoped_foundry_evidence",
        "title": payload.title,
        "summary": "Internal research candidate from declared source evidence and scenario economics.",
        "engine_id": payload.engine_id, "legacy": payload.legacy_instance_id, "jurisdiction": payload.jurisdiction,
        "required_capital": payload.startup_capital / 100, "estimated_test_cost": payload.test_cost / 100,
        "revenue_type": payload.revenue_model or {"ACQUISITION": "ACQUISITION", "DIGITAL_PRODUCT": "ONE_TIME", "SAAS": "SUBSCRIPTION",
                         "SERVICE": "SERVICE", "REAL_ESTATE": "ASSET", "OTHER": "OTHER"}[payload.kind],
        "simulation_fixture": payload.evidence_class == "SIMULATION",
        "specialist_inputs": {
            "business_id": payload.business_id, "pantheon_report_ids": [report_id],
            "foundry_evidence": {"id": str(row.id), "sha256": row.digest, "report_id": report_id},
            "foundry_economics": economics(payload),
            **({"discovery_demand": demand_evidence(payload)} if payload.provenance else {}),
            **({"consumer_research": consumer_research} if consumer_research is not None else {}),
        },
    }


def require_current_candidate(db: Session, proposal: dict, scope: dict, today: date, *,
                              advisory_only: bool = False) -> EvidenceIn | None:
    inputs = proposal.get("specialist_inputs", {})
    evidence = inputs.get("foundry_evidence")
    if evidence is None and proposal.get("source") != "scoped_foundry_evidence":
        if "consumer_research" in inputs:
            raise HTTPException(409, "Consumer research requires exact Foundry provenance")
        return
    from app.pantheon.monitor import verified_report
    from app.services.consumer_evidence import read_consumer_evidence

    try:
        row = db.get(FoundryEvidence, UUID(evidence["id"]), with_for_update=not advisory_only)
        report_id = evidence["report_id"]
        if row is None or row.digest != evidence["sha256"] or report_id not in inputs["pantheon_report_ids"]:
            raise ValueError
        payload = checked_evidence(row, scope, today, db=db)
        report = verified_report(db, report_id)
        signal = next((signal for signal in report["observations"]["foundry_signals"]
                       if signal["evidence_id"] == str(row.id) and signal["sha256"] == row.digest), None)
        research = read_consumer_evidence(db, row, payload, scope, today)
        if signal is None or signal.get("consumer_research") != research:
            raise ValueError
        canonical = candidate_fields(row, payload, report_id, consumer_research=research)
        if canonical["simulation_fixture"] and not advisory_only:
            raise HTTPException(409, "Simulated Foundry evidence stays in shadow evaluation")
        expected_inputs = canonical.pop("specialist_inputs")
        if (any(proposal.get(key) != value for key, value in canonical.items())
                or inputs.get("foundry_economics") != expected_inputs["foundry_economics"]
                or inputs.get("discovery_demand") != expected_inputs.get("discovery_demand")
                or inputs.get("consumer_research") != expected_inputs.get("consumer_research")):
            raise ValueError
        return payload
    except (AttributeError, KeyError, TypeError, ValueError):
        raise HTTPException(409, "Foundry research requires a new source-bound candidate") from None
