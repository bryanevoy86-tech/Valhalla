"""PACK 75: Integrity & Telemetry Router
API endpoints for integrity events and telemetry metrics.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional

from app.core.db import get_db
from app.services.integrity_telemetry_service import (
    log_integrity_event,
    list_integrity_events,
    log_telemetry_metric,
    list_telemetry_metrics,
)
from app.schemas.integrity_telemetry import (
    IntegrityEventOut,
    TelemetryMetricOut,
)

router = APIRouter(prefix="/integrity", tags=["Integrity & Telemetry"])


@router.post("/events", response_model=IntegrityEventOut)
def new_integrity_event(
    event_type: str,
    payload: str,
    actor: Optional[str] = None,
    signature: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Log a new integrity event."""
    return log_integrity_event(db, event_type, payload, actor, signature)


@router.get("/events", response_model=list[IntegrityEventOut])
def get_integrity_events(event_type: Optional[str] = None, db: Session = Depends(get_db)):
    """Get integrity events, optionally filtered by type."""
    return list_integrity_events(db, event_type)


@router.post("/metrics", response_model=TelemetryMetricOut)
def new_telemetry_metric(
    metric_name: str,
    value: float,
    context: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Log a new telemetry metric."""
    return log_telemetry_metric(db, metric_name, value, context)


@router.get("/metrics", response_model=list[TelemetryMetricOut])
def get_telemetry_metrics(metric_name: Optional[str] = None, db: Session = Depends(get_db)):
    """Get telemetry metrics, optionally filtered by name."""
    return list_telemetry_metrics(db, metric_name)
