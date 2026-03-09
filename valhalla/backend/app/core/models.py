"""Telemetry event models for system audit trail."""
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, JSON
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON

from app.core.db import Base


class TelemetryEvent(Base):
    """System audit trail - tracks all decisions, actions, outcomes."""
    
    __tablename__ = "telemetry_events"
    
    id = Column(String(36), primary_key=True, index=True)
    event_type = Column(String(50), nullable=False, index=True)  # decision, action, outcome, anomaly, error
    leg = Column(String(50), nullable=False, index=True)  # wholesale, fix_flip, rentbuy, etc.
    reference_id = Column(String(255), nullable=True, index=True)  # links to deal/export/job
    timestamp = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    
    # Generic payload for event-specific data
    payload = Column(SQLiteJSON, nullable=True)
    
    # Metadata for querying/filtering
    actor = Column(String(100), nullable=True)  # who triggered this (system, user, worker)
    source = Column(String(100), nullable=True)  # which system (policy_engine, worker, api)
    status = Column(String(50), nullable=True)  # success, failure, pending
    
    # Context for debugging
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f"<TelemetryEvent {self.id} ({self.event_type}/{self.leg})>"
