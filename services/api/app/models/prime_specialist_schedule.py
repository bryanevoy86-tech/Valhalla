"""Durable owner-authorized specialist schedules."""
from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, JSON, String, Uuid

from app.core.db import Base


class PrimeSpecialistSchedule(Base):
    __tablename__ = "prime_specialist_schedules"
    __table_args__ = (
        Index("ix_prime_specialist_due", "state", "next_due_at"),
        Index("ix_specialist_outcome_scope", "outcome_scope_key", "state"),
    )

    id = Column(Uuid(), primary_key=True)
    request = Column(JSON(), nullable=False)
    cadence_seconds = Column(Integer(), nullable=False)
    next_due_at = Column(DateTime(), nullable=False)
    expires_at = Column(DateTime(), nullable=False)
    state = Column(String(16), nullable=False)
    last_report_event_id = Column(String(80), nullable=True)
    outcome_scope_key = Column(String(64), nullable=True)
    pending_outcome_event_id = Column(String(80), nullable=True)


class PrimeScheduleTrigger(Base):
    __tablename__ = "prime_schedule_triggers"
    __table_args__ = (Index("ix_prime_schedule_trigger_order", "schedule_id", "queued_at", "event_id"),)
    schedule_id = Column(Uuid(), ForeignKey("prime_specialist_schedules.id", ondelete="CASCADE"), primary_key=True)
    event_id = Column(String(80), primary_key=True)
    queued_at = Column(DateTime(), nullable=False)
    failure_code = Column(String(48))
