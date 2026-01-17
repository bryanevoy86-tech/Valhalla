from sqlalchemy import Column, Integer, Float, Boolean, DateTime, Text, String, Numeric
from sqlalchemy.sql import func
from app.core.db import Base


class PolicyGateMetric(Base):
    __tablename__ = "policy_gate_metrics"
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, server_default=func.now())
    uptime_pct = Column(Float, nullable=False)
    cash_reserves = Column(Numeric(14, 2), nullable=False)
    net_margin_pct = Column(Float, nullable=False)
    audit_score = Column(Float, nullable=False)
    error_rate_ppm = Column(Integer, nullable=False)
    traffic_p90_rps = Column(Float)
    latency_p95_ms = Column(Float)


class ClonePolicy(Base):
    __tablename__ = "clone_policies"
    id = Column(Integer, primary_key=True)
    enabled = Column(Boolean, nullable=False, server_default="1")
    min_days_between = Column(Integer, nullable=False)
    max_active = Column(Integer, nullable=False)
    required_uptime_pct = Column(Float, nullable=False)
    required_cash_reserves = Column(Numeric(14, 2), nullable=False)
    required_net_margin_pct = Column(Float, nullable=False)
    required_audit_score = Column(Float, nullable=False)
    max_error_rate_ppm = Column(Integer, nullable=False)
    last_triggered_at = Column(DateTime)


class MirrorPolicy(Base):
    __tablename__ = "mirror_policies"
    id = Column(Integer, primary_key=True)
    enabled = Column(Boolean, nullable=False, server_default="1")
    min_days_between = Column(Integer, nullable=False)
    max_active = Column(Integer, nullable=False)
    required_p90_rps = Column(Float, nullable=False)
    required_p95_latency_ms = Column(Float, nullable=False)
    last_triggered_at = Column(DateTime)


class PolicyEventLog(Base):
    __tablename__ = "policy_event_logs"
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, server_default=func.now())
    kind = Column(String(32), nullable=False)
    decision = Column(String(32), nullable=False)
    reason = Column(Text, nullable=False)
    snapshot_json = Column(Text, nullable=False)
