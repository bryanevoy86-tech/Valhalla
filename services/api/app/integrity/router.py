"""Integrity router (Pack 59 + consolidation).

Exposes integrity ledger operations and a simple list endpoint over the
unified `IntegrityEvent` model (mapped to `telemetry_events`).
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.integrity.schemas import IntegrityIn, TelemetryIn
from app.integrity import service as svc
from app.integrity.models import IntegrityEvent

router = APIRouter(prefix="/integrity", tags=["integrity"])

@router.post("/event")
def add_event(body: IntegrityIn, db: Session = Depends(get_db)):
    return svc.record_integrity(db, body.actor, body.action, body.scope, body.ref_id, body.payload_json)

@router.get("/verify")
def verify(sample_last_n: int = 100, db: Session = Depends(get_db)):
    return svc.verify_chain(db, sample_last_n)

@router.post("/telemetry")
def add_telemetry(body: TelemetryIn, db: Session = Depends(get_db)):
    return svc.record_telemetry(db, body.category, body.name, body.latency_ms, body.ok, body.dim)

@router.get("/events")
def list_events(limit: int = 100, db: Session = Depends(get_db)):
    return (
        db.query(IntegrityEvent)
        .order_by(IntegrityEvent.created_at.desc())
        .limit(limit)
        .all()
    )
