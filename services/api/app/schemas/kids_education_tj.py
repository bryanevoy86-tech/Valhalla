"""
PACK TJ: Kids Education & Development Schemas
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class ChildProfileCreate(BaseModel):
    name: str
    age: Optional[int] = None
    interests: Optional[str] = None
    notes: Optional[str] = None


class ChildProfileOut(ChildProfileCreate):
    id: int

    class Config:
        from_attributes = True


class LearningPlanCreate(BaseModel):
    child_id: int
    timeframe: str
    goals: Optional[str] = None
    activities: Optional[str] = None
    parent_notes: Optional[str] = None


class LearningPlanOut(LearningPlanCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class EducationLogCreate(BaseModel):
    child_id: int
    completed_activities: Optional[str] = None
    highlights: Optional[str] = None
    parent_notes: Optional[str] = None


class EducationLogOut(EducationLogCreate):
    id: int
    date: datetime

    class Config:
        from_attributes = True


class ChildWeeklySummary(BaseModel):
    child_id: int
    child_name: str
    week_of: datetime
    completed_goals: List[str]
    fun_moments: List[str]
    growth_notes: str
