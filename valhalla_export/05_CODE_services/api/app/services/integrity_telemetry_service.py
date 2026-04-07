"""PACK 75: Integrity & Telemetry Service
Service layer for integrity events and telemetry metrics.
"""

from typing import Optional
from sqlalchemy.orm import Session

from app.models.integrity_telemetry import IntegrityEvent, TelemetryMetric


def log_integrity_event(
    db: Session,
    event_type: str,
    payload: str,
    actor: Optional[str] = None,
    signature: Optional[str] = None,
) -> IntegrityEvent:
    """Log an integrity event."""
    ev = IntegrityEvent(
        event_type=event_type,
        actor=actor,
        payload=payload,
        signature=signature,
    )
    db.add(ev)
    db.commit()
    db.refresh(ev)
    return ev


def list_integrity_events(db: Session, event_type: Optional[str] = None) -> list:
    """List integrity events, optionally filtered by type."""
    q = db.query(IntegrityEvent)
    if event_type is not None:
        q = q.filter(IntegrityEvent.event_type == event_type)
    return q.order_by(IntegrityEvent.id.desc()).all()


def log_telemetry_metric(
    db: Session,
    metric_name: str,
    value: float,
    context: Optional[str] = None,
) -> TelemetryMetric:
    """Log a telemetry metric."""
    m = TelemetryMetric(
        metric_name=metric_name,
        value=value,
        context=context,
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    return m


def list_telemetry_metrics(db: Session, metric_name: Optional[str] = None) -> list:
    """List telemetry metrics, optionally filtered by name."""
    q = db.query(TelemetryMetric)
    if metric_name is not None:
        q = q.filter(TelemetryMetric.metric_name == metric_name)
    return q.order_by(TelemetryMetric.id.desc()).all()
