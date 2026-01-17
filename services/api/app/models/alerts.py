"""PACK 73: Alerts, SLA & Rule Engine
Alert rules and event logging.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text

from app.models.base import Base


class AlertRule(Base):
    __tablename__ = "alert_rule"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    condition_payload = Column(Text, nullable=False)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AlertEvent(Base):
    __tablename__ = "alert_event"

    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(Integer, nullable=True)
    level = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
