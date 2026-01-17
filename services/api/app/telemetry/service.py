from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from app.models.telemetry import IntegrityEvent
from .schemas import TelemetryIn, TelemetryOut, TelemetryQuery
import json

class TelemetryService:
    def __init__(self, db: Session):
        self.db = db

    def write(self, body: TelemetryIn) -> TelemetryOut:
        row = IntegrityEvent(
            event=body.event,
            level=body.level,
            actor=body.actor or 'system',
            meta=json.dumps(body.meta or {})
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return TelemetryOut(id=row.id, ts=row.ts, event=row.event, level=row.level, actor=row.actor, meta=json.loads(row.meta or '{}'))

    def list(self, q: TelemetryQuery) -> List[TelemetryOut]:
        stmt = select(IntegrityEvent).order_by(desc(IntegrityEvent.id))
        if q.event:
            stmt = stmt.where(IntegrityEvent.event == q.event)
        if q.level:
            stmt = stmt.where(IntegrityEvent.level == q.level)
        if q.actor:
            stmt = stmt.where(IntegrityEvent.actor == q.actor)
        stmt = stmt.offset(q.offset).limit(min(q.limit, 500))
        rows = self.db.execute(stmt).scalars().all()
        out: List[TelemetryOut] = []
        for r in rows:
            out.append(TelemetryOut(id=r.id, ts=r.ts, event=r.event, level=r.level, actor=r.actor, meta=json.loads(r.meta or '{}')))
        return out
