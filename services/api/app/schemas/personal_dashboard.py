"""
PACK SL: Personal Master Dashboard
Pydantic schemas for life operations tracking
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class FocusAreaSchema(BaseModel):
    area_id: str = Field(..., description="Unique focus area identifier")
    name: str = Field(..., description="Focus area name")
    category: str = Field(..., description="health, family, work, education, finance, or household")
    priority_level: int = Field(5, description="1-10 priority")
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class PersonalRoutineSchema(BaseModel):
    routine_id: str = Field(..., description="Unique routine identifier")
    focus_area_id: Optional[int] = None
    name: str = Field(..., description="Routine name")
    description: Optional[str] = None
    frequency: str = Field(..., description="daily, weekly, or monthly")
    notes: Optional[str] = None
    status: str = Field("active", description="active or paused")

    class Config:
        from_attributes = True


class RoutineCompletionSchema(BaseModel):
    completion_id: str = Field(..., description="Unique completion identifier")
    routine_id: int
    date: datetime
    completed: int = Field(..., description="0 or 1 (boolean)")
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class FamilySnapshotSchema(BaseModel):
    snapshot_id: str = Field(..., description="Unique snapshot identifier")
    date: datetime
    kids_notes: Optional[List[Dict[str, Any]]] = Field(None, description="[{name, education, mood, interests}]")
    partner_notes: Optional[str] = Field(None, description="User-provided only")
    home_operations: Optional[str] = None
    highlights: Optional[List[str]] = None

    class Config:
        from_attributes = True


class LifeDashboardSchema(BaseModel):
    dashboard_id: str = Field(..., description="Unique dashboard identifier")
    week_of: datetime = Field(..., description="Week starting date")
    wins: Optional[List[str]] = None
    challenges: Optional[List[str]] = None
    habits_tracked: Optional[List[Dict[str, Any]]] = Field(None, description="[{habit, completion_rate}]")
    upcoming_priorities: Optional[List[str]] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class PersonalGoalSchema(BaseModel):
    goal_id: str = Field(..., description="Unique goal identifier")
    name: str = Field(..., description="Goal name")
    description: Optional[str] = None
    category: str = Field(..., description="health, education, finance, family, etc.")
    deadline: Optional[datetime] = None
    progress_percent: int = Field(0, description="0-100")
    status: str = Field("active", description="active, completed, or paused")
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class MoodLogSchema(BaseModel):
    log_id: str = Field(..., description="Unique mood log identifier")
    date: datetime
    mood: str = Field(..., description="excellent, good, neutral, challenging, or difficult")
    energy_level: Optional[int] = Field(None, description="1-10")
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class LifeOperationsResponse(BaseModel):
    week_of: datetime
    total_focus_areas: int
    active_routines: int
    week_completion_rate: float
    family_snapshot_current: Optional[bool]
    goals_on_track: int
    goals_total: int
