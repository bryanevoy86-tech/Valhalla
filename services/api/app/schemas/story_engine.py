"""
PACK AA: Story Engine Schemas
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class StoryTemplateBase(BaseModel):
    arc_name: str = Field(..., description="Story arc / series name")
    audience: Optional[str] = Field(None, description="child, adult, family, etc.")
    tone: Optional[str] = Field(None, description="funny, epic, cozy, etc.")
    purpose: Optional[str] = Field(None, description="bedtime, encouragement, lesson, etc.")
    prompt: str = Field(..., description="Prompt or seed description for Heimdall")
    outline: Optional[str] = Field(None, description="Optional structured outline")


class StoryTemplateCreate(StoryTemplateBase):
    pass


class StoryTemplateUpdate(BaseModel):
    arc_name: Optional[str] = None
    audience: Optional[str] = None
    tone: Optional[str] = None
    purpose: Optional[str] = None
    prompt: Optional[str] = None
    outline: Optional[str] = None
    is_active: Optional[bool] = None


class StoryTemplateOut(StoryTemplateBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class StoryEpisodeCreate(BaseModel):
    template_id: int
    child_id: Optional[int] = None
    title: Optional[str] = None
    content: str
    mood: Optional[str] = None
    length_estimate_minutes: Optional[int] = None


class StoryEpisodeOut(BaseModel):
    id: int
    template_id: int
    child_id: Optional[int]
    title: Optional[str]
    content: str
    mood: Optional[str]
    length_estimate_minutes: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True
