"""Publish verified internal outcomes to exact-scope advisory subscriptions."""
import hashlib
import json
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import inspect, literal, select
from sqlalchemy.dialects.postgresql import insert as postgres_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.models.prime_specialist_schedule import PrimeScheduleTrigger, PrimeSpecialistSchedule
from app.models.specialist_assignment import SpecialistAssignment, SpecialistTrigger


def outcome_scope_key(scope: dict) -> str:
    return hashlib.sha256(json.dumps(scope, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def enqueue_prime(db: Session, scope_key: str, event_id: str, now: datetime, *, subscription: str,
                  opportunity_id: str | None = None) -> None:
    schedule = PrimeSpecialistSchedule
    inspector = inspect(db.connection())
    if inspector.has_table(schedule.__tablename__):
        columns = {column["name"] for column in inspector.get_columns(schedule.__tablename__)}
        if {"outcome_scope_key", "pending_outcome_event_id"} <= columns:
            targets = select(schedule.id, literal(event_id), literal(now)).where(
                schedule.outcome_scope_key == scope_key, schedule.state == "active", schedule.expires_at > now,
                schedule.request[subscription].as_boolean().is_(True),
            )
            if opportunity_id is not None:
                targets = targets.where(schedule.request["opportunity"]["opportunity_id"].as_string() == opportunity_id)
            store_triggers(db, PrimeScheduleTrigger, "schedule_id", targets)


def publish_verified_outcome(db: Session, scope: dict, event_id: str) -> None:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    scope_key = outcome_scope_key(scope)
    enqueue_prime(db, scope_key, event_id, now, subscription="on_verified_outcome")
    enqueue_research(db, scope_key, event_id, now)


def enqueue_research(db: Session, scope_key: str, event_id: str, now: datetime, *, roles=None) -> None:
    assignment = SpecialistAssignment
    schema = inspect(db.connection())
    if not schema.has_table(assignment.__tablename__):
        return
    targets = select(assignment.id, literal(event_id), literal(now)).where(
        assignment.scope_key == scope_key, assignment.state == "active", assignment.expires_at > now,
    )
    if roles is not None:
        targets = targets.where(assignment.role.in_(roles))
    store_triggers(db, SpecialistTrigger, "assignment_id", targets)


def store_triggers(db: Session, model, parent_key: str, targets) -> None:
    connection = db.connection()
    if not inspect(connection).has_table(model.__tablename__):
        raise HTTPException(503, "Specialist trigger queue schema not ready")
    insert = {"postgresql": postgres_insert, "sqlite": sqlite_insert}.get(connection.dialect.name)
    if insert is None:
        raise HTTPException(503, "Specialist trigger queue database unsupported")
    with db.no_autoflush:
        db.execute(insert(model).from_select(
            [parent_key, "event_id", "queued_at"], targets,
        ).on_conflict_do_nothing(index_elements=[parent_key, "event_id"]))
