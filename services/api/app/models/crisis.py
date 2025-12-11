"""
PACK TH: Crisis Management Models
Profiles crises, step-by-step plans, and logs.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from app.core.db import Base


class CrisisProfile(Base):
    __tablename__ = "crisis_profiles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=True)  # family, financial, health, legal, operations
    description = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    steps = relationship("CrisisActionStep", back_populates="crisis", cascade="all, delete-orphan")
    logs = relationship("CrisisLogEntry", back_populates="crisis", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<CrisisProfile(name={self.name}, category={self.category})>"


class CrisisActionStep(Base):
    __tablename__ = "crisis_action_steps"

    id = Column(Integer, primary_key=True, index=True)
    crisis_id = Column(Integer, ForeignKey("crisis_profiles.id"), nullable=False)
    order = Column(Integer, nullable=True)
    action = Column(Text, nullable=False)
    responsible_role = Column(String, nullable=True)  # KING, QUEEN, ODIN, etc.
    notes = Column(Text, nullable=True)

    crisis = relationship("CrisisProfile", back_populates="steps")

    def __repr__(self):
        return f"<CrisisActionStep(order={self.order}, action={self.action[:30]}...)>"


class CrisisLogEntry(Base):
    __tablename__ = "crisis_log_entries"

    id = Column(Integer, primary_key=True, index=True)
    crisis_id = Column(Integer, ForeignKey("crisis_profiles.id"), nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    event = Column(Text, nullable=False)
    actions_taken = Column(Text, nullable=True)
    active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)

    crisis = relationship("CrisisProfile", back_populates="logs")

    def __repr__(self):
        return f"<CrisisLogEntry(event={self.event[:30]}..., active={self.active})>"
