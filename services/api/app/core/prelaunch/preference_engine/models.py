"""PACK-CORE-PRELAUNCH-01: Preference Engine - Models"""

from datetime import datetime
from enum import Enum

from sqlalchemy import Column, DateTime, Integer, String, Boolean, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.models.base import Base


class DetailLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class OverwhelmResponse(str, Enum):
    SIMPLIFY = "SIMPLIFY"
    PAUSE = "PAUSE"
    REASSURE = "REASSURE"


class PreferenceProfile(Base):
    __tablename__ = "preference_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    directness = Column(Integer, default=7)  # 1-10
    empathy_weight = Column(Integer, default=5)  # 1-10
    detail_level = Column(SAEnum(DetailLevel), default=DetailLevel.MEDIUM)
    push_level = Column(Integer, default=7)  # 1-10
    show_alternatives = Column(Boolean, default=True)
    max_concurrent_tasks = Column(Integer, default=3)
    overwhelm_response = Column(
        SAEnum(OverwhelmResponse), default=OverwhelmResponse.SIMPLIFY
    )

    preferred_morning_time = Column(String(8), nullable=True)  # "07:30"
    preferred_night_time = Column(String(8), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
