"""PACK 67: Story Video Engine (Core Layer)
Powers animated stories, educational videos, and empire updates.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text

from app.models.base import Base


class StoryVideo(Base):
    __tablename__ = "story_video"

    id = Column(Integer, primary_key=True, index=True)
    source_module = Column(String, nullable=False)
    script_payload = Column(Text, nullable=False)
    status = Column(String, default="queued")
    output_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
