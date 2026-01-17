"""
PACK AX: Feature Flags Schemas
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class FeatureFlagCreate(BaseModel):
    key: str = Field(..., description="Unique flag key, e.g. 'kids_story_mode'")
    name: str
    description: Optional[str] = None
    enabled: bool = False
    audience: Optional[str] = Field(None, description="global, kids, family, founders, etc.")
    variant: Optional[str] = Field(None, description="A, B, etc.")


class FeatureFlagUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None
    audience: Optional[str] = None
    variant: Optional[str] = None


class FeatureFlagOut(BaseModel):
    id: int
    key: str
    name: str
    description: Optional[str]
    enabled: bool
    audience: Optional[str]
    variant: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
