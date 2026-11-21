"""Intake owner-authorized Foundry evidence and prepare research candidates."""
from datetime import datetime, timezone
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.dependencies import require_prime_control_key
from app.loki.evidence import artifact_digest
from app.models.completion_registry import SourceRegistryItem
from app.models.foundry_evidence import FoundryEvidence
from app.pantheon.monitor import verified_report
from app.services.foundry_discovery import (
    DISCOVERY_ROLES, EvidenceIn, SCOPE_FIELDS, candidate_fields, checked_evidence, withdrawal_trigger,
)
from app.services.foundry_intake import FoundryIntakeJob, Intake, current_time, intake_ready, job_view, key_for, source_for
from app.services.prime_business_execution import _check_legacy, require_owner_mandate_key
from app.services.specialist_triggers import enqueue_prime, enqueue_research, outcome_scope_key


def schema(db: Session = Depends(get_db)):
    if not inspect(db.connection()).has_table(FoundryEvidence.__tablename__):
        raise HTTPException(503, "Foundry evidence schema unavailable")


router = APIRouter(prefix="/api/prime/foundry", tags=["foundry-discovery"],
                   dependencies=[Depends(require_prime_control_key), Depends(schema)])
owner = [Depends(require_owner_mandate_key)]


@router.post("/evidence", status_code=201, dependencies=owner)
def record_evidence(request: EvidenceIn, db: Session = Depends(get_db)):
    scope = request.model_dump(include=SCOPE_FIELDS)
    _check_legacy(db, **scope)
    if request.observed_on > datetime.now(timezone.utc).date():
        raise HTTPException(422, "Observed date is in the future")
    # Preserve the exact payload shape and digest of historical records without acquisition terms.
    if request.provenance is not None:
        raise HTTPException(422, "Discovery provenance is assigned by the intake worker")
    payload = request.model_dump(mode="json", exclude_none=True)
    digest = artifact_digest("foundry_evidence", str(request.evidence_id), payload)
    row = db.get(FoundryEvidence, request.evidence_id)
    if row:
        if row.digest != digest:
            raise HTTPException(409, "Foundry evidence ID already used")
        return {"evidence_id": row.id, "sha256": row.digest, "revoked": row.revoked}
    row = FoundryEvidence(id=request.evidence_id, scope_key=outcome_scope_key(scope),
                          source_ref=request.source_ref, observed_on=request.observed_on,
                          expires_on=request.expires_on, payload=payload, digest=digest)
    db.add(row)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Foundry evidence ID or observation already used") from None
    return {"evidence_id": row.id, "sha256": row.digest, "revoked": row.revoked}


@router.delete("/evidence/{evidence_id}", dependencies=owner)
def revoke_evidence(evidence_id: UUID, db: Session = Depends(get_db)):
    row = db.get(FoundryEvidence, evidence_id, with_for_update=True)
    if row is None:
        raise HTTPException(404, "Foundry evidence not found")
    if not row.revoked:
        row.revoked = True
        at = current_time().replace(tzinfo=None)
        event = withdrawal_trigger(row)
        enqueue_research(db, row.scope_key, event, at, roles=DISCOVERY_ROLES)
        enqueue_prime(db, row.scope_key, event, at, subscription="on_economic_reassessment")
        db.commit()
    return {"evidence_id": row.id, "revoked": True}


@router.get("/reports/{report_id}/candidate/{evidence_id}")
def prepare_candidate(report_id: str, evidence_id: UUID, db: Session = Depends(get_db)):
    report = verified_report(db, report_id)
    row = db.get(FoundryEvidence, evidence_id)
    if row is None or not any(
        signal["evidence_id"] == str(evidence_id) and signal["sha256"] == row.digest
        for signal in report.get("observations", {}).get("foundry_signals", [])
    ):
        raise HTTPException(404, "Report does not contain this research candidate")
    _check_legacy(db, **report["scope"])
    payload = checked_evidence(row, report["scope"], datetime.now(timezone.utc).date(), db=db)
    return {"proposal": {**candidate_fields(row, payload, report_id), "persist_decision": False},
            "state": "RESEARCH_CANDIDATE", "execution_authorized": False}


@router.post("/intake", status_code=202, dependencies=owner)
def queue_intake(request: Intake, db: Session = Depends(get_db)):
    if not intake_ready(db):
        raise HTTPException(503, "Discovery intake not migrated")
    now = current_time()
    _check_legacy(db, **request.evidence.model_dump(include=SCOPE_FIELDS))
    source_for(db, request, now.date(), lock=True, verify_enrollment_time=True)
    payload = request.model_dump(mode="json", exclude_none=True)
    job_id = request.evidence.evidence_id
    digest = artifact_digest("foundry_intake", str(job_id), payload)
    prior = db.get(FoundryIntakeJob, job_id)
    if prior is not None:
        if prior.digest != digest:
            raise HTTPException(409, "Discovery job ID already used")
        return job_view(prior)
    observation_key = key_for(request)
    if db.scalar(select(FoundryIntakeJob.id).filter_by(observation_key=observation_key)) is not None:
        raise HTTPException(409, "Source observation already queued")
    job = FoundryIntakeJob(id=job_id, observation_key=observation_key, digest=digest, payload=payload,
                           status="QUEUED", attempts=0, next_attempt_at=now)
    db.add(job)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Discovery job or source observation already used") from None
    return job_view(job)


@router.get("/intake/{job_id}")
def read_intake(job_id: UUID, db: Session = Depends(get_db)):
    if not intake_ready(db):
        raise HTTPException(503, "Discovery intake not migrated")
    job = db.get(FoundryIntakeJob, job_id)
    if job is None:
        raise HTTPException(404, "Discovery job not found")
    if job.digest != artifact_digest("foundry_intake", str(job.id), job.payload):
        raise HTTPException(409, "Discovery job evidence failed integrity")
    scope = Intake.model_validate(job.payload).evidence.model_dump(include=SCOPE_FIELDS)
    _check_legacy(db, **scope)
    return job_view(job)


class SourceSigningKey(BaseModel):
    model_config = ConfigDict(extra="forbid")
    public_key_hex: str = Field(pattern=r"^[0-9a-f]{64}$")
    previous_public_key_hex: str | None = Field(None, pattern=r"^[0-9a-f]{64}$")


@router.put("/intake/sources/{source_id}/signing-key", dependencies=owner)
def enroll_signing_key(source_id: str, request: SourceSigningKey, db: Session = Depends(get_db)):
    if not intake_ready(db):
        raise HTTPException(503, "Discovery intake not migrated")
    source = db.scalar(select(SourceRegistryItem).filter_by(source_id=source_id).with_for_update())
    if source is None or source.source_type.upper() not in {"DEMAND_EXPORT", "PROCUREMENT_EXPORT"}:
        raise HTTPException(404, "Eligible discovery source not found")
    proposed = f"ed25519:{request.public_key_hex}"
    if source.provenance_method == proposed:
        return {"source_id": source_id, "signature_required": True}
    current = source.provenance_method
    if current and current != f"ed25519:{request.previous_public_key_hex}":
        raise HTTPException(409, "Existing source provenance does not match the expected key")
    if not current and request.previous_public_key_hex:
        raise HTTPException(409, "Prior source signing key not found")
    source.provenance_method = proposed
    db.commit()
    return {"source_id": source_id, "signature_required": True}
