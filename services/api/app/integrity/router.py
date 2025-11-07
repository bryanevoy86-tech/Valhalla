"""Integrity router (Pack 59)"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.integrity.schemas import *
from app.integrity import service as svc

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
