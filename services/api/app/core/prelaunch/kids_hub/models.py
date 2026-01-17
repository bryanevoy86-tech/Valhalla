"""Kids Hub Models"""
from datetime import datetime
from sqlalchemy import Column, DateTime, JSON, String
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.models.base import Base


class PrelaunchKidsHubChildProfile(Base):
    """Child profile with preferences and metadata."""
    __tablename__ = "children_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(128), nullable=False, index=True)
    nickname = Column(String(128), nullable=True)
    age = Column(String(16), nullable=True)
    preferences = Column(JSON, nullable=True)  # {"favorite_topics": [...], ...}
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)


class ChildTask(Base):
    """Tasks/quests for children."""
    __tablename__ = "children_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    child_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(String, nullable=True)
    status = Column(String(32), default="PENDING")  # PENDING / DONE
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
