"""
PACK AS: Empire Journal Engine Models
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text
from app.models.base import Base


class JournalEntry(Base):
    """Master journal of the empire with internal notes, insights, and lessons."""
    __tablename__ = "journal_entries"

    id = Column(Integer, primary_key=True, index=True)

    # what this entry is about
    entity_type = Column(String, nullable=True)   # deal, property, child, system, self, etc.
    entity_id = Column(String, nullable=True)

    category = Column(String, nullable=False, default="note")
    # note, insight, lesson, risk, win, idea, task_context

    author = Column(String, nullable=True)        # bryan, lanna, heimdall, va_1, etc.

    title = Column(String, nullable=True)
    body = Column(Text, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)
