"""
PACK CI8: Narrative / Chapter Engine Models
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Boolean
from app.models.base import Base


class NarrativeChapter(Base):
    """
    Major 'chapter' of your life/system.
    Example: 'Foundation', 'First Million', 'Custody Battle', etc.
    """
    __tablename__ = "narrative_chapters"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    slug = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=True)
    phase_order = Column(Integer, nullable=False, default=1)

    goals = Column(JSON, nullable=True)
    exit_conditions = Column(JSON, nullable=True)  # conditions to move to next chapter

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class NarrativeEvent(Base):
    """
    Key event in the story.
    """
    __tablename__ = "narrative_events"

    id = Column(Integer, primary_key=True, index=True)
    chapter_id = Column(Integer, nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)
    occurred_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class ActiveChapter(Base):
    """
    Current active chapter pointer.
    """
    __tablename__ = "active_chapters"

    id = Column(Integer, primary_key=True, index=True, default=1)
    chapter_id = Column(Integer, nullable=False)
    changed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    reason = Column(Text, nullable=True)
