"""Publish verified internal outcomes to exact-scope advisory subscriptions."""
import hashlib
import json
from datetime import datetime, timezone

from sqlalchemy import inspect, update
from sqlalchemy.orm import Session

from app.models.prime_specialist_schedule import PrimeSpecialistSchedule


def outcome_scope_key(scope: dict) -> str:
    return hashlib.sha256(json.dumps(scope, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def publish_verified_outcome(db: Session, scope: dict, event_id: str) -> None:
    schedule = PrimeSpecialistSchedule
    inspector = inspect(db.connection())
    if not inspector.has_table(schedule.__tablename__):
        return
    columns = {column["name"] for column in inspector.get_columns(schedule.__tablename__)}
    if not {"outcome_scope_key", "pending_outcome_event_id"} <= columns:
        return

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    db.execute(
        update(schedule)
        .where(
            schedule.outcome_scope_key == outcome_scope_key(scope),
            schedule.state == "active",
            schedule.expires_at > now,
        )
        .values(pending_outcome_event_id=event_id)
    )
