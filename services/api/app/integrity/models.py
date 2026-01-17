from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from app.core.db import Base


class IntegrityEvent(Base):
    """
    Integrity / telemetry event log entry.

    This is mapped to the existing `telemetry_events` table so we don't
    duplicate models under a different name.
    """

    __tablename__ = "telemetry_events"

    id = Column(Integer, primary_key=True, index=True)

    # When the event was recorded
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)

    # High level category of the event (e.g. "security", "compliance", "system")
    event_type = Column(String(100), nullable=False, index=True)

    # Where it came from (e.g. "heimdall-core", "weweb-api", "worker", "user-action")
    source = Column(String(100), nullable=True, index=True)

    # Severity / level (info, warning, error, critical)
    level = Column(String(50), nullable=False, default="info", index=True)

    # Human-readable description of what happened
    message = Column(Text, nullable=True)

    # Raw structured payload for extra context (request data, headers, etc.)
    payload = Column(JSON, nullable=True)

    # For tying events together across systems (request id, job id, etc.)
    correlation_id = Column(String(255), nullable=True, index=True)


__all__ = ["IntegrityEvent", "TelemetryEvent", "TelemetryCounter"]

# Backwards-compatibility aliases for older imports expecting legacy telemetry models
TelemetryEvent = IntegrityEvent
TelemetryCounter = IntegrityEvent
