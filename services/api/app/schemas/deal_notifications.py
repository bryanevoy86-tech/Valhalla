"""
Schemas for deal notifications.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class DealNotificationIn(BaseModel):
    type: str = Field(..., description="Event type: analysis_complete, moved_to_pipeline, marked_dead, disposition_updated")
    message: Optional[str] = Field(None, description="Optional custom message")


class DealNotificationOut(BaseModel):
    id: int
    deal_id: Optional[int] = None
    type: str
    title: str
    message: Optional[str] = None
    created_at: datetime
    is_read: bool

    class Config:
        from_attributes = True
