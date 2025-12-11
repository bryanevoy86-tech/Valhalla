"""PACK 86: Narrative Documentary Engine - Records
Records empire's journey—milestones, achievements, setbacks.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime

from app.models.base import Base


class NarrativeEvent(Base):
    __tablename__ = "narrative_event"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    emotion_level = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class NarrativeChapter(Base):
    __tablename__ = "narrative_chapter"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    chapter_payload = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
