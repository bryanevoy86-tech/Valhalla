from __future__ import annotations

from uuid import uuid4
from datetime import datetime, timezone
from fastapi import APIRouter
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.core.models import TelemetryEvent
from .schemas import TelemetryEventIn

router = APIRouter(prefix="/telemetry", tags=["telemetry"])


@router.post("/event")
def ingest_event(evt: TelemetryEventIn):
    """Ingest telemetry event and persist to database."""
    db = SessionLocal()
    try:
        event = TelemetryEvent(
            id=uuid4().hex,
            event_type=evt.event_type,
            leg=evt.leg,
            reference_id=evt.reference_id,
            timestamp=datetime.now(timezone.utc),
            payload=evt.payload,
            actor=evt.actor,
            source=evt.source,
            status=evt.status,
            error_message=evt.error_message,
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return {
            "ok": True,
            "id": event.id,
            "timestamp": event.timestamp,
        }
    except Exception as e:
        db.rollback()
        return {"ok": False, "error": str(e)}
    finally:
        db.close()
