"""Persistent scoped assignments for independently polled Pantheon roles."""
from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, JSON, String, UniqueConstraint, Uuid

from app.core.db import Base


class SpecialistAssignment(Base):
    __tablename__ = "prime_specialist_assignments"
    __table_args__ = (
        UniqueConstraint("role", "scope_key", name="uq_specialist_role_scope"),
        Index("ix_specialist_assignment_due", "role", "state", "next_due_at"),
        Index("ix_specialist_assignment_scope", "scope_key", "state"),
    )
    id = Column(Uuid(), primary_key=True)
    role = Column(String(40), nullable=False)
    scope_key = Column(String(64), nullable=False)
    scope = Column(JSON(), nullable=False)
    cadence_seconds = Column(Integer(), nullable=False)
    next_due_at = Column(DateTime(), nullable=False)
    expires_at = Column(DateTime(), nullable=False)
    state = Column(String(20), nullable=False)
    pending_event_id = Column(String(80))
    last_report_event_id = Column(String(80))


class SpecialistTrigger(Base):
    __tablename__ = "prime_specialist_triggers"
    __table_args__ = (Index("ix_specialist_trigger_order", "assignment_id", "queued_at", "event_id"),)
    assignment_id = Column(Uuid(), ForeignKey("prime_specialist_assignments.id", ondelete="CASCADE"), primary_key=True)
    event_id = Column(String(80), primary_key=True)
    queued_at = Column(DateTime(), nullable=False)
    failure_code = Column(String(48))
