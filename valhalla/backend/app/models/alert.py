from sqlalchemy import JSON, TIMESTAMP, Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from ..core.db import Base


class Schedule(Base):
    __tablename__ = "schedules"
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("orgs.id", ondelete="CASCADE"), index=True, nullable=True)
    name = Column(String, nullable=False)
    kind = Column(String, nullable=False, default="interval")
    spec = Column(JSON, nullable=False)
    task = Column(String, nullable=False)
    params = Column(JSON, nullable=True)
    next_run_at = Column(TIMESTAMP(timezone=True), index=True, nullable=True)
    active = Column(Boolean, default=True, index=True)
    last_error = Column(Text, nullable=True)


class AlertRule(Base):
    __tablename__ = "alert_rules"
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("orgs.id", ondelete="CASCADE"), index=True, nullable=False)
    name = Column(String, nullable=False)
    condition = Column(JSON, nullable=False)
    severity = Column(String, nullable=False, default="warn")
    channels = Column(JSON, nullable=False, default=list)
    dedupe_key = Column(String, nullable=True)
    active = Column(Boolean, default=True, index=True)


class AlertEvent(Base):
    __tablename__ = "alert_events"
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, index=True, nullable=False)
    rule_id = Column(
        Integer, ForeignKey("alert_rules.id", ondelete="SET NULL"), index=True, nullable=True
    )
    fired_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), index=True)
    payload = Column(JSON, nullable=True)
    severity = Column(String, nullable=False, default="warn")
    dedupe_key = Column(String, nullable=True)


class SLATimer(Base):
    __tablename__ = "sla_timers"
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, index=True, nullable=False)
    resource = Column(String, nullable=False)
    due_at = Column(TIMESTAMP(timezone=True), index=True, nullable=False)
    status = Column(String, nullable=False, default="open")
    rule = Column(String, nullable=True)
    meta = Column(JSON, nullable=True)
