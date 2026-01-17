"""
PACK TK: Life Timeline & Milestones Schemas
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class LifeEventCreate(BaseModel):
    date: Optional[datetime] = None
    title: str
    category: Optional[str] = None
    description: Optional[str] = None
    impact_level: Optional[int] = None
    notes: Optional[str] = None


class LifeEventOut(LifeEventCreate):
    id: int
    date: datetime

    class Config:
        from_attributes = True


class LifeMilestoneCreate(BaseModel):
    event_id: Optional[int] = None
    milestone_type: str
    description: str
    notes: Optional[str] = None


class LifeMilestoneOut(LifeMilestoneCreate):
    id: int

    class Config:
        from_attributes = True


class LifeTimelineSnapshot(BaseModel):
    from_date: datetime
    to_date: datetime
    events: List[LifeEventOut]
    milestones: List[LifeMilestoneOut]
