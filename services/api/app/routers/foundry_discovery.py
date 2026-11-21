"""Intake owner-authorized Foundry evidence and prepare research candidates."""
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.dependencies import require_prime_control_key
from app.loki.evidence import artifact_digest
from app.models.foundry_evidence import FoundryEvidence
from app.pantheon.monitor import verified_report
from app.services.foundry_discovery import EvidenceIn, SCOPE_FIELDS, candidate_fields, checked_evidence
from app.services.prime_business_execution import _check_legacy, require_owner_mandate_key
from app.services.specialist_triggers import outcome_scope_key


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
    payload = request.model_dump(mode="json")
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
    row.revoked = True
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
    payload = checked_evidence(row, report["scope"], datetime.now(timezone.utc).date())
    return {"proposal": {**candidate_fields(row, payload, report_id), "persist_decision": False},
            "state": "RESEARCH_CANDIDATE", "execution_authorized": False}
