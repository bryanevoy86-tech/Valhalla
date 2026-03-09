"""
Telemetry events model for tracking system activity and errors.
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
