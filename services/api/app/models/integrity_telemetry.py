"""PACK 75: Integrity & Telemetry Engine
Integrity event logging and telemetry metrics.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Float

from app.models.base import Base


class IntegrityEvent(Base):
    __tablename__ = "integrity_event"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String, nullable=False)
    actor = Column(String, nullable=True)
    payload = Column(Text, nullable=False)
    signature = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class TelemetryMetric(Base):
    __tablename__ = "telemetry_metric"

    id = Column(Integer, primary_key=True, index=True)
    metric_name = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    context = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
