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
DISCOVERY_ROLES = frozenset({"ODIN", "HUGINN", "NJORD", "FREYJA", "TYR", "FORSETI"})


class EvidenceIn(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    evidence_id: UUID
    legacy_instance_id: str = Field(min_length=3, max_length=80)
    business_id: str = Field(min_length=3, max_length=120)
    engine_id: str = Field(min_length=3, max_length=80)
    jurisdiction: str = Field(min_length=2, max_length=80)
    kind: Literal["ACQUISITION", "DIGITAL_PRODUCT", "SAAS", "SERVICE", "REAL_ESTATE"]
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

    @model_validator(mode="after")
    def validate_dates(self):
        if not self.observed_on <= self.expires_on <= self.observed_on + timedelta(days=366):
            raise ValueError("Invalid evidence validity dates")
        return self


def economics(payload: EvidenceIn) -> dict:
    contribution = payload.unit_price - payload.variable_cost_per_unit - payload.acquisition_cost_per_unit
    estimated = contribution * payload.monthly_units - payload.monthly_fixed_cost
    stressed_units = payload.monthly_units * 3 // 4
    return {
        "basis": "DECLARED_INPUTS_ONLY", "currency": payload.currency,
        "monthly_units": payload.monthly_units, "unit_contribution_minor": contribution,
        "break_even_units": ((payload.monthly_fixed_cost + contribution - 1) // contribution if contribution > 0 else None),
        "estimated_monthly_operating_contribution_minor": estimated,
        "stress_monthly_units": stressed_units,
        "stress_monthly_operating_contribution_minor": contribution * stressed_units - payload.monthly_fixed_cost,
        "declared_startup_capital_minor": payload.startup_capital, "declared_validation_cost_minor": payload.test_cost,
        "verified_revenue_minor": None,
    }


def checked_evidence(row: FoundryEvidence, scope: dict, today: date) -> EvidenceIn:
    if (row.scope_key != outcome_scope_key(scope) or row.revoked
            or not row.observed_on <= today <= row.expires_on
            or row.digest != artifact_digest("foundry_evidence", str(row.id), row.payload)):
        raise HTTPException(409, "Foundry evidence is stale, revised or outside scope")
    payload = EvidenceIn.model_validate(row.payload)
    if (payload.model_dump(include=SCOPE_FIELDS) != scope or payload.observed_on != row.observed_on
            or payload.expires_on != row.expires_on or payload.source_ref != row.source_ref):
        raise HTTPException(409, "Foundry evidence metadata has changed")
    return payload


def review_priority(role: str, metrics: dict) -> str:
    if role in {"TYR", "FORSETI", "HUGINN"}:
        return "VERIFY_SOURCE_AND_RIGHTS"
    if role == "FREYJA":
        return "VALIDATE_DEMAND_AND_ACQUISITION_COST"
    contribution = metrics["estimated_monthly_operating_contribution_minor"]
    if metrics["unit_contribution_minor"] <= 0 or contribution < 0:
        return "INVESTIGATE_UNVIABLE_ECONOMICS"
    if metrics["stress_monthly_operating_contribution_minor"] < 0:
        return "INVESTIGATE_VOLUME_SENSITIVITY"
    return "VALIDATE_DECLARED_ECONOMICS"


def discover(db: Session, role: str, scope: dict, today: date) -> dict:
    if not inspect(db.connection()).has_table(FoundryEvidence.__tablename__):
        return {"foundry_signal_status": "SOURCE_SCHEMA_UNAVAILABLE", "foundry_signals": []}
    rows = db.scalars(select(FoundryEvidence).where(
        FoundryEvidence.scope_key == outcome_scope_key(scope),
        FoundryEvidence.revoked.is_(False),
        FoundryEvidence.observed_on <= today, FoundryEvidence.expires_on >= today,
    ).order_by(FoundryEvidence.observed_on.desc(), FoundryEvidence.id).limit(20)).all()
    signals = []
    rejected = []
    for row in rows:
        try:
            payload = checked_evidence(row, scope, today)
        except (HTTPException, ValueError):
            rejected.append(str(row.id))
            continue
        metrics = economics(payload)
        signals.append({
            "evidence_id": str(row.id), "sha256": row.digest, "source_ref": row.source_ref,
            "title": payload.title, "kind": payload.kind, "evidence_class": payload.evidence_class,
            "priority": review_priority(role, metrics), "economics": metrics,
        })
    return {"foundry_signal_status": "OBSERVED" if signals else "NO_ELIGIBLE_SOURCE",
            "foundry_signals": signals, "invalid_foundry_evidence_ids": rejected}


def candidate_fields(row: FoundryEvidence, payload: EvidenceIn, report_id: str) -> dict:
    return {
        "opportunity_id": f"foundry-{row.id}",
        "source": "scoped_foundry_evidence",
        "title": payload.title,
        "summary": "Internal research candidate from declared source evidence and scenario economics.",
        "engine_id": payload.engine_id, "legacy": payload.legacy_instance_id, "jurisdiction": payload.jurisdiction,
        "required_capital": payload.startup_capital / 100, "estimated_test_cost": payload.test_cost / 100,
        "revenue_type": {"ACQUISITION": "ACQUISITION", "DIGITAL_PRODUCT": "ONE_TIME", "SAAS": "SUBSCRIPTION",
                         "SERVICE": "SERVICE", "REAL_ESTATE": "ASSET"}[payload.kind],
        "simulation_fixture": payload.evidence_class == "SIMULATION",
        "specialist_inputs": {
            "business_id": payload.business_id, "pantheon_report_ids": [report_id],
            "foundry_evidence": {"id": str(row.id), "sha256": row.digest, "report_id": report_id},
            "foundry_economics": economics(payload),
        },
    }


def require_current_candidate(db: Session, proposal: dict, scope: dict, today: date) -> None:
    inputs = proposal.get("specialist_inputs", {})
    evidence = inputs.get("foundry_evidence")
    if evidence is None and proposal.get("source") != "scoped_foundry_evidence":
        return
    from app.pantheon.monitor import verified_report

    try:
        row = db.get(FoundryEvidence, UUID(evidence["id"]), with_for_update=True)
        report_id = evidence["report_id"]
        if row is None or row.digest != evidence["sha256"] or report_id not in inputs["pantheon_report_ids"]:
            raise ValueError
        payload = checked_evidence(row, scope, today)
        report = verified_report(db, report_id)
        if not any(signal["evidence_id"] == str(row.id) and signal["sha256"] == row.digest
                   for signal in report["observations"]["foundry_signals"]):
            raise ValueError
        canonical = candidate_fields(row, payload, report_id)
        if canonical["simulation_fixture"]:
            raise HTTPException(409, "Simulated Foundry evidence stays in shadow evaluation")
        expected_inputs = canonical.pop("specialist_inputs")
        if (any(proposal.get(key) != value for key, value in canonical.items())
                or inputs.get("foundry_economics") != expected_inputs["foundry_economics"]):
            raise ValueError
    except (AttributeError, KeyError, TypeError, ValueError):
        raise HTTPException(409, "Foundry research requires a new source-bound candidate") from None
