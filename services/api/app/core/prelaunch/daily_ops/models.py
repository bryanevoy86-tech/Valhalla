"""PACK-CORE-PRELAUNCH-01: Daily Ops - Models"""

from datetime import date, datetime

from sqlalchemy import Column, Date, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.models.base import Base


class DailySnapshot(Base):
    __tablename__ = "daily_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    snapshot_date = Column(Date, nullable=False, index=True)
    financial_summary = Column(JSON, nullable=True)
    risk_summary = Column(JSON, nullable=True)
    tasks_today = Column(JSON, nullable=True)
    alerts_summary = Column(JSON, nullable=True)
    notes = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class NightlySnapshot(Base):
    __tablename__ = "nightly_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    snapshot_date = Column(Date, nullable=False, index=True)
    completed_tasks = Column(JSON, nullable=True)
    missed_tasks = Column(JSON, nullable=True)
    projection_changes = Column(JSON, nullable=True)
    risk_changes = Column(JSON, nullable=True)
    notes = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
