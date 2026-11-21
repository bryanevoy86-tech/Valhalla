"""Schedule scoped shadow intelligence using the canonical Prime evaluator."""
import hashlib
import json
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import inspect, or_, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.dependencies import require_prime_control_key
from app.models.completion_registry import LegacyOrchestrationEvent
from app.models.prime_specialist_schedule import PrimeSpecialistSchedule
from app.routers.completion_registry import (
    UniversalOpportunityBatchIn, UniversalOpportunityIn, _validate_phase3_opportunity,
    evaluate_universal_opportunities,
)
from app.routers.prime_business_factory import require_factory_schema
from app.services.prime_business_execution import (
    _check_legacy, _emergency_stop_active, _event, require_owner_mandate_key,
    verified_internal_outcomes,
)

from app.services.specialist_triggers import outcome_scope_key


REPORT_EVENT = "PRIME_SPECIALIST_SHADOW_REPORT"


def require_schedule_schema(db: Session = Depends(get_db)):
    require_factory_schema(db)
    inspector = inspect(db.get_bind())
    required = ("prime_specialist_schedules", "learning_feedback_records", "knowledge_registry_items")
    if any(not inspector.has_table(name) for name in required):
        raise HTTPException(status_code=503, detail="Specialist scheduling schema not ready")
    columns = {column["name"] for column in inspector.get_columns(PrimeSpecialistSchedule.__tablename__)}
    if not {"outcome_scope_key", "pending_outcome_event_id"} <= columns:
        raise HTTPException(status_code=503, detail="Specialist scheduling schema not ready")


router = APIRouter(
    prefix="/api/prime/specialist-schedules", tags=["prime-specialist-schedules"],
    dependencies=[Depends(require_prime_control_key), Depends(require_schedule_schema)],
)


class ScheduleIn(BaseModel):
    schedule_id: UUID
    business_id: str = Field(min_length=3, max_length=120)
    opportunity: UniversalOpportunityIn
    cadence_seconds: int = Field(ge=300, le=86400, strict=True)
    duration_seconds: int = Field(ge=300, le=2592000, strict=True)
    on_verified_outcome: bool = False


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _scope(payload: ScheduleIn) -> dict:
    return {
        "legacy_instance_id": payload.opportunity.legacy,
        "business_id": payload.business_id,
        "engine_id": payload.opportunity.engine_id,
        "jurisdiction": payload.opportunity.jurisdiction,
    }


def _lookup(db: Session, schedule_id: UUID) -> PrimeSpecialistSchedule:
    row = db.get(PrimeSpecialistSchedule, schedule_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Specialist schedule not found")
    return row


def _report(db: Session, schedule_id: UUID, event_id: str) -> dict | None:
    event = db.query(LegacyOrchestrationEvent).filter_by(event_id=event_id, event_type=REPORT_EVENT).one_or_none()
    report = json.loads(event.payload_json) if event else None
    return report if report and report["schedule_id"] == str(schedule_id) else None


def _describe(db: Session, row: PrimeSpecialistSchedule) -> dict:
    report = _report(db, row.id, row.last_report_event_id) if row.last_report_event_id else None
    return {
        "schedule_id": row.id,
        "state": "expired" if row.state == "active" and row.expires_at <= _utc_now() else row.state,
        "next_due_at": row.next_due_at.replace(tzinfo=timezone.utc),
        "expires_at": row.expires_at.replace(tzinfo=timezone.utc),
        "latest_report": report,
        "on_verified_outcome": row.outcome_scope_key is not None,
    }


@router.post("", status_code=201, dependencies=[Depends(require_owner_mandate_key)])
def create_schedule(payload: ScheduleIn, db: Session = Depends(get_db)):
    opportunity = payload.opportunity
    if not opportunity.jurisdiction or opportunity.replay_partition or opportunity.historical_outcome is not None:
        raise HTTPException(status_code=422, detail="Supply a current opportunity in a registered jurisdiction")
    if not opportunity.human_approval_required or opportunity.independent_loki_review_id is not None:
        raise HTTPException(status_code=422, detail="Schedule requires human approval and carries no independent review")
    _validate_phase3_opportunity(opportunity)
    normalized = payload.model_copy(update={
        "opportunity": opportunity.model_copy(update={
            "persist_decision": False, "specialist_inputs": {**opportunity.specialist_inputs, "business_id": payload.business_id},
        }),
    })
    request = normalized.model_dump(mode="json")
    if len(json.dumps(request).encode("utf-8")) > 65536:
        raise HTTPException(status_code=413, detail="Schedule inputs exceed 64 KiB")
    _check_legacy(db, **_scope(normalized))
    now = _utc_now()
    row = PrimeSpecialistSchedule(
        id=payload.schedule_id, request=request, cadence_seconds=payload.cadence_seconds,
        next_due_at=now, expires_at=now + timedelta(seconds=payload.duration_seconds), state="active",
        outcome_scope_key=outcome_scope_key(_scope(normalized)) if payload.on_verified_outcome else None,
    )
    db.add(row)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        row = _lookup(db, payload.schedule_id)
        if {"on_verified_outcome": False, **row.request} != request:
            raise HTTPException(status_code=409, detail="Schedule ID already has a different mandate")
    return _describe(db, row)


@router.get("/{schedule_id}")
def read_schedule(schedule_id: UUID, db: Session = Depends(get_db)):
    return _describe(db, _lookup(db, schedule_id))


@router.get("/{schedule_id}/reports/{report_event_id}")
def read_report(schedule_id: UUID, report_event_id: str, db: Session = Depends(get_db)):
    report = _report(db, schedule_id, report_event_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Specialist report not found")
    return report


@router.delete("/{schedule_id}", dependencies=[Depends(require_owner_mandate_key)])
def cancel_schedule(schedule_id: UUID, db: Session = Depends(get_db)):
    _lookup(db, schedule_id)
    db.execute(update(PrimeSpecialistSchedule).where(PrimeSpecialistSchedule.id == schedule_id).values(state="cancelled"))
    db.commit()
    return _describe(db, _lookup(db, schedule_id))


def run_due_schedule(db: Session, *, now: datetime | None = None) -> dict:
    """Run one due slot. A report and cursor advance commit as one transaction."""
    require_schedule_schema(db)
    if _emergency_stop_active(db):
        return {"status": "blocked", "emergency_stop": True}
    now = now if now is not None else _utc_now()
    row = (
        db.query(PrimeSpecialistSchedule)
        .filter_by(state="active")
        .filter(
            PrimeSpecialistSchedule.expires_at > now,
            or_(PrimeSpecialistSchedule.next_due_at <= now, PrimeSpecialistSchedule.pending_outcome_event_id.is_not(None)),
        )
        .order_by(PrimeSpecialistSchedule.next_due_at, PrimeSpecialistSchedule.id)
        .with_for_update(skip_locked=True)
        .first()
    )
    if row is None:
        return {"status": "idle"}
    # Coalesce missed slots after downtime. Preserve the original cadence.
    timed = row.next_due_at <= now
    outcome_id = row.pending_outcome_event_id
    elapsed_slots = (now - row.next_due_at) // timedelta(seconds=row.cadence_seconds) if timed else 0
    slot = row.next_due_at.replace(tzinfo=timezone.utc).isoformat() if timed else None
    occurrence = slot if timed else outcome_id
    report_id = "SPECIALIST-" + hashlib.sha256(f"{row.id}/{occurrence}".encode()).hexdigest()
    payload = ScheduleIn.model_validate(row.request)
    scope = _scope(payload)
    report = {
        "schedule_id": str(row.id), "report_event_id": report_id, "scheduled_for": slot,
        "observed_at": now.replace(tzinfo=timezone.utc).isoformat(), "scope": scope,
        "external_authority": False, "independent_loki_cleared": False,
        "effect": "ADVISORY_ONLY", "missed_slots_coalesced": elapsed_slots,
        "trigger": "VERIFIED_OUTCOME" if outcome_id else "CADENCE",
        "trigger_outcome_event_id": outcome_id,
    }
    try:
        _check_legacy(db, **scope)
        outcomes = verified_internal_outcomes(db, **scope)
        if outcome_id and not any(item["outcome_event_id"] == outcome_id for item in outcomes):
            raise HTTPException(status_code=409, detail="Trigger outcome evidence failed revalidation")
        result = evaluate_universal_opportunities(UniversalOpportunityBatchIn(
            opportunities=[payload.opportunity], shadow_mode=True, persist_decision=False,
        ), db)
        report.update(
            status="evaluated", evaluation=result["evaluations"][0],
            recommendation=result["owner_recommendation"],
            verified_internal_outcomes=outcomes,
        )
    except (HTTPException, ValidationError) as exc:
        report.update(status="blocked", reason=exc.detail if isinstance(exc, HTTPException) else "Invalid specialist inputs")
    _event(
        db, event_id=report_id, legacy_instance_id=scope["legacy_instance_id"], event_type=REPORT_EVENT,
        message=f"Prime specialist schedule {report['status']}", payload=jsonable_encoder(report),
    )
    if timed:
        row.next_due_at += timedelta(seconds=(elapsed_slots + 1) * row.cadence_seconds)
    row.pending_outcome_event_id = None
    row.last_report_event_id = report_id
    db.commit()
    return {"status": report["status"], "report_event_id": report_id}
