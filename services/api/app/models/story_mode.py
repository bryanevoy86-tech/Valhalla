"""
PACK AV: Narrative Story Mode Models
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text
from app.models.base import Base


class StoryPrompt(Base):
    """Story prompts for kids, family, founders with themes like adventure, learning, bedtime."""
    __tablename__ = "story_prompts"

    id = Column(Integer, primary_key=True, index=True)

    audience = Column(String, nullable=True)   # kids, family, founders, ops, etc.
    theme = Column(String, nullable=True)      # adventure, learning, bedtime, empire, etc.

    title = Column(String, nullable=True)
    prompt_text = Column(Text, nullable=False)

    created_by = Column(String, nullable=True)  # bryan, lanna, heimdall, child_name
    created_at = Column(DateTime, default=datetime.utcnow)


class StoryOutput(Base):
    """Generated story outputs from prompts."""
    __tablename__ = "story_outputs"

    id = Column(Integer, primary_key=True, index=True)

    prompt_id = Column(Integer, nullable=True)
    audience = Column(String, nullable=True)
    theme = Column(String, nullable=True)

    title = Column(String, nullable=True)
    body = Column(Text, nullable=False)

    created_by = Column(String, nullable=True)  # heimdall, bryan, etc.
    created_at = Column(DateTime, default=datetime.utcnow)
