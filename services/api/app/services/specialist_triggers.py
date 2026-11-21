"""Publish verified internal outcomes to exact-scope advisory subscriptions."""
import hashlib
import json
from datetime import datetime, timezone

from sqlalchemy import inspect, update
from sqlalchemy.orm import Session

from app.models.prime_specialist_schedule import PrimeSpecialistSchedule
from app.models.specialist_assignment import SpecialistAssignment


def outcome_scope_key(scope: dict) -> str:
    return hashlib.sha256(json.dumps(scope, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def publish_verified_outcome(db: Session, scope: dict, event_id: str) -> None:
    schedule = PrimeSpecialistSchedule
    inspector = inspect(db.connection())
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    scope_key = outcome_scope_key(scope)
    if inspector.has_table(schedule.__tablename__):
        columns = {column["name"] for column in inspector.get_columns(schedule.__tablename__)}
        if {"outcome_scope_key", "pending_outcome_event_id"} <= columns:
            db.execute(update(schedule).where(
                schedule.outcome_scope_key == scope_key, schedule.state == "active", schedule.expires_at > now,
            ).values(pending_outcome_event_id=event_id))
    assignment = SpecialistAssignment
    if inspector.has_table(assignment.__tablename__):
        db.execute(update(assignment).where(
            assignment.scope_key == scope_key, assignment.state == "active", assignment.expires_at > now,
        ).values(pending_event_id=event_id))
