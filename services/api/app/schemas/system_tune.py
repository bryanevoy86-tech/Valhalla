"""
PACK TF: System Tune List Engine Schemas
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class TuneItemCreate(BaseModel):
    title: str = Field(..., description="Item title")
    description: Optional[str] = Field(None, description="Details")
    priority: Optional[int] = Field(None, ge=1, le=5, description="1–5 priority")
    status: Optional[str] = Field("pending", description="pending, in_progress, done, skipped")


class TuneItemOut(TuneItemCreate):
    id: int
    area_id: int
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TuneAreaCreate(BaseModel):
    name: str = Field(..., description="Area name")
    description: Optional[str] = Field(None, description="What this area covers")


class TuneAreaOut(TuneAreaCreate):
    id: int
    items: List[TuneItemOut] = []

    class Config:
        from_attributes = True
