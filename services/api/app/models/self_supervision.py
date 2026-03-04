"""
PACK CL13: Self-Supervision & Drift Findings
Tracks Heimdall self-audit runs and the findings produced.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Boolean
from app.models.base import Base


class SelfSupervisionRun(Base):
    __tablename__ = "self_supervision_runs"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String, unique=True, index=True, nullable=False)

    # Optional: what triggered this run ("weekly_audit", "manual", "post_close", etc.)
    trigger = Column(String, nullable=True)

    # Scope hint: what did we audit ("decisions", "leads", "compliance", "all")
    scope = Column(String, nullable=True)

    # High level summary
    summary = Column(Text, nullable=True)

    # Structured metrics (counts, rates, drift %, etc.)
    metrics = Column(JSON, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class SelfSupervisionFinding(Base):
    __tablename__ = "self_supervision_findings"

    id = Column(Integer, primary_key=True, index=True)

    run_id = Column(String, index=True, nullable=False)

    # "logic_drift", "data_gap", "policy_risk", "integration_break", "quality"
    finding_type = Column(String, nullable=False)

    severity = Column(String, nullable=False, default="medium")  # low/medium/high/critical

    title = Column(String, nullable=False)
    detail = Column(Text, nullable=True)

    # Optional structured context
    context = Column(JSON, nullable=True)

    # Mark when it was addressed
    resolved = Column(Boolean, nullable=False, default=False)
    resolved_notes = Column(Text, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
