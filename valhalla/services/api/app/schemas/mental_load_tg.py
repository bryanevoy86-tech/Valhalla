"""
PACK TG: Mental Load Offloading Schemas
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class MentalLoadEntryCreate(BaseModel):
    category: str
    description: str
    urgency_level: Optional[int] = None
    emotional_weight: Optional[int] = None
    action_required: bool = False


class MentalLoadEntryOut(MentalLoadEntryCreate):
    id: int
    created_at: datetime
    archived: bool

    class Config:
        from_attributes = True


class MentalLoadSummaryCreate(BaseModel):
    date: datetime
    notes: Optional[str] = None


class MentalLoadSummaryOut(BaseModel):
    id: int
    date: datetime
    total_items: int
    urgent_items: int
    action_items: int
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class MentalLoadDailyView(BaseModel):
    date: datetime
    entries: List[MentalLoadEntryOut]
    summary: Optional[MentalLoadSummaryOut] = None
