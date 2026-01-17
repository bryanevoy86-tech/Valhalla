"""Story Admin Schemas"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class StorySettingsRead(BaseModel):
    id: UUID
    default_length_minutes: int
    allow_comedy: bool
    allow_action: bool
    allow_emotional_focus: bool
    learning_focus: Optional[list[str]] = None
    bedtime_soft_mode: bool
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StorySettingsUpdate(BaseModel):
    default_length_minutes: Optional[int] = None
    allow_comedy: Optional[bool] = None
    allow_action: Optional[bool] = None
    allow_emotional_focus: Optional[bool] = None
    learning_focus: Optional[list[str]] = None
    bedtime_soft_mode: Optional[bool] = None


class StorySessionRead(BaseModel):
    id: UUID
    child_id: UUID
    child_name: Optional[str] = None
    mode: str
    title: Optional[str] = None
    theme: Optional[str] = None
    summary: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
