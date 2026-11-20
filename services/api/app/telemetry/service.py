from sqlalchemy import select
from sqlalchemy.orm import Session

from app.integrity.models import IntegrityEvent

from .schemas import TelemetryIn, TelemetryOut, TelemetryQuery


def _out(row: IntegrityEvent) -> TelemetryOut:
    return TelemetryOut(
        id=row.id, ts=row.created_at, event=row.event_type, level=row.level,
        actor=row.source, meta=row.payload if isinstance(row.payload, dict) else {},
    )


class TelemetryService:
    def __init__(self, db: Session):
        self.db = db

    def write(self, body: TelemetryIn) -> TelemetryOut:
        row = IntegrityEvent(event_type=body.event, level=body.level, source=body.actor or "system", payload=body.meta)
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return _out(row)

    def list(self, query: TelemetryQuery) -> list[TelemetryOut]:
        stmt = select(IntegrityEvent).order_by(IntegrityEvent.id.desc())
        if query.event:
            stmt = stmt.where(IntegrityEvent.event_type == query.event)
        if query.level:
            stmt = stmt.where(IntegrityEvent.level == query.level)
        if query.actor:
            stmt = stmt.where(IntegrityEvent.source == query.actor)
        stmt = stmt.offset(query.offset).limit(min(query.limit, 500))
        return [_out(row) for row in self.db.scalars(stmt)]
