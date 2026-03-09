"""
PACK AA: Story Engine Models
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base


class StoryTemplate(Base):
    __tablename__ = "story_templates"

    id = Column(Integer, primary_key=True, index=True)

    # e.g. "Valhalla Chronicles", "Heimdall Bot Pizza Night"
    arc_name = Column(String, nullable=False)
    audience = Column(String, nullable=True)      # child, adult, family, etc.
    tone = Column(String, nullable=True)          # funny, epic, cozy, etc.
    purpose = Column(String, nullable=True)       # bedtime, encouragement, learning, etc.

    # Prompt/outline Heimdall can use
    prompt = Column(Text, nullable=False)
    outline = Column(Text, nullable=True)

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    episodes = relationship(
        "StoryEpisode",
        back_populates="template",
        cascade="all, delete-orphan",
    )


class StoryEpisode(Base):
    __tablename__ = "story_episodes"

    id = Column(Integer, primary_key=True, index=True)

    template_id = Column(Integer, ForeignKey("story_templates.id"), nullable=False)
    # optional link to children hub user/child id if you want it
    child_id = Column(Integer, nullable=True)

    # Concrete story text Heimdall told
    title = Column(String, nullable=True)
    content = Column(Text, nullable=False)

    # basic metadata
    mood = Column(String, nullable=True)
    length_estimate_minutes = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    template = relationship("StoryTemplate", back_populates="episodes")
