"""
PACK SW: Life Timeline & Major Milestones Engine

Models for capturing life events, milestones, and timeline snapshots.
This provides Heimdall with a structured, factual record of your life story.
"""

from sqlalchemy import Column, Integer, String, Date, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base


class LifeEvent(Base):
    """
    Captures major life events with factual description and user-defined impact.
    """
    __tablename__ = "life_event"

    id = Column(Integer, primary_key=True)
    event_id = Column(String(32), unique=True, nullable=False)  # Prefix: lifevnt
    date = Column(Date, nullable=False)
    title = Column(String(255), nullable=False)
    category = Column(String(32), nullable=False)  # personal, family, business, financial, health, achievement
    description = Column(Text, nullable=False)
    impact_level = Column(Integer, nullable=False, default=1)  # 1-5 user-defined
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    milestones = relationship("LifeMilestone", back_populates="event", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<LifeEvent {self.event_id}: {self.title}>"


class LifeMilestone(Base):
    """
    Marks specific milestones within a life event.
    """
    __tablename__ = "life_milestone"

    id = Column(Integer, primary_key=True)
    milestone_id = Column(String(32), unique=True, nullable=False)  # Prefix: lifemile
    event_id = Column(Integer, ForeignKey("life_event.id", ondelete="CASCADE"), nullable=False)
    milestone_type = Column(String(32), nullable=False)  # start, finish, transition, achievement
    description = Column(Text, nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    event = relationship("LifeEvent", back_populates="milestones")

    def __repr__(self):
        return f"<LifeMilestone {self.milestone_id}: {self.milestone_type}>"


class LifeTimelineSnapshot(Base):
    """
    Captures a periodic snapshot of major events, recent changes, and upcoming milestones.
    """
    __tablename__ = "life_timeline_snapshot"

    id = Column(Integer, primary_key=True)
    snapshot_id = Column(String(32), unique=True, nullable=False)  # Prefix: snapshot
    date_generated = Column(Date, nullable=False)
    major_events = Column(JSON, nullable=False, default=[])  # List of event IDs
    recent_changes = Column(JSON, nullable=False, default=[])  # List of recent descriptions
    upcoming_milestones = Column(JSON, nullable=False, default=[])  # List of milestone descriptions
    user_notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<LifeTimelineSnapshot {self.snapshot_id}: {self.date_generated}>"
