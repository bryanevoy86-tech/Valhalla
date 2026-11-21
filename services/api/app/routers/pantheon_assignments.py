"""Manage independent read-only specialist subscriptions."""
from datetime import timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.dependencies import require_prime_control_key
from app.models.specialist_assignment import SpecialistAssignment
from app.pantheon.monitor import assignment_schema, utc_now, verified_report
from app.pantheon.roles import LENSES, Role
from app.services.prime_business_execution import _check_legacy, require_owner_mandate_key
from app.services.specialist_triggers import outcome_scope_key


def require_schema(db: Session = Depends(get_db)):
    assignment_schema(db)


router = APIRouter(
    prefix="/api/prime/pantheon", tags=["pantheon-assignments"],
    dependencies=[Depends(require_prime_control_key), Depends(require_schema)],
)
owner = [Depends(require_owner_mandate_key)]


class Timing(BaseModel):
    model_config = ConfigDict(extra="forbid")
    cadence_seconds: int = Field(ge=60, le=86400, strict=True)
    duration_seconds: int = Field(ge=300, le=2592000, strict=True)


class AssignmentIn(Timing):
    assignment_id: UUID
    role: Role
    legacy_instance_id: str = Field(min_length=3, max_length=80)
    business_id: str = Field(min_length=3, max_length=120)
    jurisdiction: str = Field(min_length=2, max_length=80)
    engine_id: str = Field(min_length=3, max_length=80)


def info(row):
    return {
        "assignment_id": row.id, "role": row.role, "scope": row.scope, "lens": LENSES[row.role],
        "state": ("expired" if row.state == "active" and row.expires_at <= utc_now() else row.state),
        "cadence_seconds": row.cadence_seconds, "next_due_at": row.next_due_at.isoformat() + "Z",
        "expires_at": row.expires_at.isoformat() + "Z", "latest_report_id": row.last_report_event_id,
        "external_authority": False,
    }


@router.get("/roles")
def roles():
    return {"local_monitoring_lenses": LENSES, "inference_status": "NO_AUTOMATIC_PROVIDER_DISPATCH"}


@router.post("/assignments", status_code=201, dependencies=owner)
def enroll(payload: AssignmentIn, db: Session = Depends(get_db)):
    scope = payload.model_dump(include={"legacy_instance_id", "business_id", "engine_id", "jurisdiction"})
    _check_legacy(db, **scope)
    current = db.get(SpecialistAssignment, payload.assignment_id)
    if current is not None:
        if (current.scope, current.role, current.cadence_seconds) != (scope, payload.role, payload.cadence_seconds):
            raise HTTPException(409, "Assignment ID already used")
        return info(current)
    now = utc_now()
    row = SpecialistAssignment(
        id=payload.assignment_id, scope=scope, scope_key=outcome_scope_key(scope),
        role=payload.role, cadence_seconds=payload.cadence_seconds,
        next_due_at=now, expires_at=now + timedelta(seconds=payload.duration_seconds), state="active",
    )
    db.add(row)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Role already assigned to this scope") from None
    return info(row)


def get_assignment(db, assignment_id, *, lock=False):
    row = db.get(SpecialistAssignment, assignment_id, with_for_update=lock)
    if row is None:
        raise HTTPException(404, "Specialist assignment not found")
    return row


@router.get("/assignments/{assignment_id}")
def read_assignment(assignment_id: UUID, db: Session = Depends(get_db)):
    return info(get_assignment(db, assignment_id))


@router.put("/assignments/{assignment_id}/renew", dependencies=owner)
def renew(assignment_id: UUID, payload: Timing, db: Session = Depends(get_db)):
    row = get_assignment(db, assignment_id, lock=True)
    _check_legacy(db, **row.scope)
    now = utc_now()
    row.next_due_at = now
    row.expires_at = now + timedelta(seconds=payload.duration_seconds)
    row.cadence_seconds = payload.cadence_seconds
    row.state = "active"
    db.commit()
    return info(row)


@router.delete("/assignments/{assignment_id}", dependencies=owner)
def revoke(assignment_id: UUID, db: Session = Depends(get_db)):
    row = get_assignment(db, assignment_id, lock=True)
    row.state = "revoked"
    row.pending_event_id = None
    db.commit()
    return info(row)


@router.get("/reports/{event_id}")
def read_report(event_id: str, db: Session = Depends(get_db)):
    return verified_report(db, event_id)


@router.post("/reports/{event_id}/challenge", status_code=201)
def challenge_report(event_id: str, db: Session = Depends(get_db)):
    from app.loki.specialist_review import enqueue_report

    review = enqueue_report(db, event_id)
    return {"review_id": review.id, "artifact_sha256": review.artifact_sha256, "status": review.status}
