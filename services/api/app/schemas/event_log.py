"""
PACK AH: Event Log / Timeline Engine Schemas
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class EventLogCreate(BaseModel):
    entity_type: str = Field(..., description="deal, property, child, professional, etc.")
    entity_id: Optional[str] = Field(None, description="ID of the entity, as string")
    event_type: str = Field(..., description="event type key")
    source: Optional[str] = Field(None, description="system, heimdall, user, va, worker, etc.")
    title: Optional[str] = None
    description: Optional[str] = None


class EventLogOut(BaseModel):
    id: int
    entity_type: str
    entity_id: Optional[str]
    event_type: str
    source: Optional[str]
    title: Optional[str]
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
