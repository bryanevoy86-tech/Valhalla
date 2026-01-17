"""Story Admin Models"""
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Index
from sqlalchemy.dialects.postgresql import UUID, JSON
import uuid

from app.models.base import Base


class StorySettings(Base):
    """Story engine global settings."""
    
    __tablename__ = "story_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    default_length_minutes = Column(Integer, default=20, nullable=False)
    allow_comedy = Column(Boolean, default=True, nullable=False)
    allow_action = Column(Boolean, default=True, nullable=False)
    allow_emotional_focus = Column(Boolean, default=True, nullable=False)
    learning_focus = Column(JSON, nullable=True)  # list of tags
    bedtime_soft_mode = Column(Boolean, default=True, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_story_settings_updated_at", "updated_at"),
    )


class StorySession(Base):
    """Story session history and metadata."""
    
    __tablename__ = "story_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    child_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    child_name = Column(String(128), nullable=True)
    mode = Column(String(32), nullable=False)  # BEDTIME / LEARNING / FUN
    title = Column(String(255), nullable=True)
    theme = Column(String(128), nullable=True)
    summary = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)

    __table_args__ = (
        Index("ix_story_sessions_child_id", "child_id"),
        Index("ix_story_sessions_created_at", "created_at"),
    )
