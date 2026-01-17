"""PACK-CORE-PRELAUNCH-01: Preference Engine - Schemas"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from .models import DetailLevel, OverwhelmResponse


class PreferenceProfileBase(BaseModel):
    directness: int = 7
    empathy_weight: int = 5
    detail_level: DetailLevel = DetailLevel.MEDIUM
    push_level: int = 7
    show_alternatives: bool = True
    max_concurrent_tasks: int = 3
    overwhelm_response: OverwhelmResponse = OverwhelmResponse.SIMPLIFY
    preferred_morning_time: Optional[str] = None
    preferred_night_time: Optional[str] = None


class PreferenceProfileRead(PreferenceProfileBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PreferenceProfileUpdate(BaseModel):
    directness: Optional[int] = None
    empathy_weight: Optional[int] = None
    detail_level: Optional[DetailLevel] = None
    push_level: Optional[int] = None
    show_alternatives: Optional[bool] = None
    max_concurrent_tasks: Optional[int] = None
    overwhelm_response: Optional[OverwhelmResponse] = None
    preferred_morning_time: Optional[str] = None
    preferred_night_time: Optional[str] = None
