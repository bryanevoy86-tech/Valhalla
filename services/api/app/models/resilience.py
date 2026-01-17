"""
PACK TD: Resilience & Recovery Planner Models
Tracks setbacks, recovery plans, and concrete actions.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from app.core.db import Base


class SetbackEvent(Base):
    __tablename__ = "setback_events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    category = Column(String, nullable=True)  # financial, family, health, system, etc.
    description = Column(Text, nullable=True)
    severity = Column(Integer, nullable=True)  # 1–5 user-defined
    date = Column(DateTime, default=datetime.utcnow)
    resolved = Column(Boolean, default=False)

    recovery_plans = relationship("RecoveryPlan", back_populates="setback", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<SetbackEvent(title={self.title}, severity={self.severity}, resolved={self.resolved})>"


class RecoveryPlan(Base):
    __tablename__ = "recovery_plans"

    id = Column(Integer, primary_key=True, index=True)
    setback_id = Column(Integer, ForeignKey("setback_events.id"), nullable=False)
    name = Column(String, nullable=False)
    goal = Column(Text, nullable=True)
    status = Column(String, default="active")  # active, paused, completed
    created_at = Column(DateTime, default=datetime.utcnow)

    setback = relationship("SetbackEvent", back_populates="recovery_plans")
    actions = relationship("RecoveryAction", back_populates="plan", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<RecoveryPlan(name={self.name}, status={self.status})>"


class RecoveryAction(Base):
    __tablename__ = "recovery_actions"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("recovery_plans.id"), nullable=False)
    description = Column(Text, nullable=False)
    order = Column(Integer, nullable=True)
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)

    plan = relationship("RecoveryPlan", back_populates="actions")

    def __repr__(self):
        return f"<RecoveryAction(description={self.description[:30]}, completed={self.completed})>"
