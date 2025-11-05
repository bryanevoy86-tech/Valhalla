"""
Telemetry models for tracking system activity and errors.

This module now contains:
- TelemetryEvent: legacy model for "telemetry_events"
- IntegrityEvent: Pack 9 model for the Integrity Ledger ("integrity_events")
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, func
from ..core.db import Base


class TelemetryEvent(Base):
    __tablename__ = "telemetry_events"
    
    id = Column(Integer, primary_key=True)
    kind = Column(String(80), nullable=False)  # e.g., "build", "ingest", "error"
    message = Column(Text, nullable=True)
    meta_json = Column(Text, nullable=True)  # JSON string for additional metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class IntegrityEvent(Base):
    """Pack 9: Integrity Ledger events"""
    __tablename__ = "integrity_events"

    id = Column(Integer, primary_key=True, index=True)
    ts = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    event = Column(String(200), nullable=False, index=True)
    level = Column(String(16), nullable=False, server_default="info", index=True)
    actor = Column(String(120), nullable=False, server_default="system", index=True)
    meta = Column(Text, nullable=False, server_default="{}")
