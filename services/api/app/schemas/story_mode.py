"""
PACK AV: Narrative Story Mode Schemas
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class StoryPromptCreate(BaseModel):
    audience: Optional[str] = Field(None, description="kids, family, founders, etc.")
    theme: Optional[str] = Field(None, description="adventure, learning, bedtime, etc.")
    title: Optional[str] = None
    prompt_text: str
    created_by: Optional[str] = None


class StoryPromptOut(BaseModel):
    id: int
    audience: Optional[str]
    theme: Optional[str]
    title: Optional[str]
    prompt_text: str
    created_by: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class StoryOutputCreate(BaseModel):
    prompt_id: Optional[int] = None
    audience: Optional[str] = None
    theme: Optional[str] = None
    title: Optional[str] = None
    body: str
    created_by: Optional[str] = None


class StoryOutputOut(BaseModel):
    id: int
    prompt_id: Optional[int]
    audience: Optional[str]
    theme: Optional[str]
    title: Optional[str]
    body: str
    created_by: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
