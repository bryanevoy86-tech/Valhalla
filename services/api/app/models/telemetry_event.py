"""
PACK L0-06: Telemetry Event Model
Centralized telemetry event storage for system observability.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, JSON, Index

from app.models.base import Base


class TelemetryEvent(Base):
    """
    Centralized telemetry event store.
    
    All system events (health, logs, security, jobs, etc.) are recorded here
    for observability, tracing, and audit trails.
    
    Marked as stable schema (STABLE CONTRACT).
    """
    
    __tablename__ = "telemetry_events"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Core event identification
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    event_type = Column(String(100), nullable=False, index=True)  # e.g., "health.check", "log.write", "job.complete"
    source = Column(String(100), nullable=False, index=True)  # e.g., "system_health", "job_runner", "security"
    
    # Severity and categorization
    severity = Column(String(20), nullable=False, default="info")  # debug, info, warning, error, critical
    category = Column(String(50), nullable=True, index=True)  # auth, security, finance, system, etc.
    
    # Distributed tracing
    correlation_id = Column(String(100), nullable=True, index=True)  # trace across requests
    parent_trace_id = Column(String(100), nullable=True)  # parent span ID
    
    # Tenant & Actor isolation
    tenant_id = Column(String(100), nullable=True, index=True)
    actor_id = Column(String(100), nullable=True, index=True)  # user, system, job runner, etc.
    actor_type = Column(String(50), nullable=True)  # "user", "system", "job", "ai"
    
    # Payload & context
    message = Column(String(500), nullable=True)
    payload = Column(JSON, nullable=True)  # Structured data (no secrets, no PII)
    
    # Metadata
    duration_ms = Column(Integer, nullable=True)  # How long did this operation take?
    status = Column(String(50), nullable=True)  # "ok", "error", "timeout", etc.
    
    # Indexing for common queries
    __table_args__ = (
        Index("idx_timestamp_severity", "timestamp", "severity"),
        Index("idx_event_source", "event_type", "source"),
        Index("idx_correlation", "correlation_id", "timestamp"),
        Index("idx_tenant_actor", "tenant_id", "actor_id"),
    )
    
    def __repr__(self) -> str:
        return (
            f"<TelemetryEvent(id={self.id}, event_type={self.event_type}, "
            f"source={self.source}, severity={self.severity}, "
            f"timestamp={self.timestamp})>"
        )
