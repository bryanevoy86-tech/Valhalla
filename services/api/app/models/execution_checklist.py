"""
PACK CL15: Execution Checklist
Tracks build/run readiness tasks that must be green before activation.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from app.models.base import Base


class ExecutionChecklistItem(Base):
    __tablename__ = "execution_checklist_items"

    id = Column(Integer, primary_key=True, index=True)

    key = Column(String, unique=True, index=True, nullable=False)  # e.g. "db_migrations_applied"
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    is_complete = Column(Boolean, nullable=False, default=False)
    completed_notes = Column(Text, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
