from __future__ import annotations

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Index
from app.models.base import Base


class FollowupTask(Base):
    """
    Enforced follow-up ladder tasks.
    """
    __tablename__ = "followup_task"

    id = Column(Integer, primary_key=True, index=True)

    lead_id = Column(String, nullable=True)  # if you have a lead table, store its id; else keep flexible
    province = Column(String, nullable=True)
    market = Column(String, nullable=True)

    channel = Column(String, nullable=False)  # SMS/CALL/EMAIL
    step = Column(Integer, nullable=False, default=1)

    due_at = Column(DateTime, nullable=False)
    completed = Column(Boolean, nullable=False, default=False)
    completed_at = Column(DateTime, nullable=True)

    owner = Column(String, nullable=True)  # "bryan", "va1", etc.
    note = Column(Text, nullable=True)

    correlation_id = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


Index("ix_followup_due_completed", FollowupTask.due_at, FollowupTask.completed)
