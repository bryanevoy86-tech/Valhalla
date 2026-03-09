"""
PACK SM: Kids Education & Development Engine
Pydantic schemas for learning plans and education tracking
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ChildProfileSchema(BaseModel):
    child_id: str = Field(..., description="Unique child identifier")
    name: str = Field(..., description="Child name")
    age: int = Field(..., description="Child age in years")
    interests: Optional[List[str]] = Field(None, description="List of child interests")
    skill_levels: Optional[Dict[str, str]] = Field(None, description="User-defined skill levels")
    notes: Optional[str] = Field(None, description="Parent notes about child")
    
    class Config:
        from_attributes = True


class LearningGoalSchema(BaseModel):
    goal: str = Field(..., description="Learning goal")
    notes: Optional[str] = Field(None, description="Notes about goal")


class LearningActivitySchema(BaseModel):
    activity: str = Field(..., description="Activity description")
    category: str = Field(..., description="Activity category")
    duration_minutes: Optional[int] = Field(None, description="Duration in minutes")


class LearningPlanSchema(BaseModel):
    plan_id: str = Field(..., description="Unique plan identifier")
    child_id: int = Field(..., description="Child ID from profile")
    timeframe: str = Field(..., description="daily, weekly, or monthly")
    goals: Optional[List[LearningGoalSchema]] = Field(None, description="Learning goals")
    activities: Optional[List[LearningActivitySchema]] = Field(None, description="Planned activities")
    parent_notes: Optional[str] = Field(None, description="Parent notes")
    status: Optional[str] = Field(None, description="active, completed, or paused")
    
    class Config:
        from_attributes = True


class EducationLogSchema(BaseModel):
    log_id: str = Field(..., description="Unique log identifier")
    child_id: int = Field(..., description="Child ID")
    date: datetime = Field(..., description="Date of education activity")
    completed_activities: Optional[List[str]] = Field(None, description="Completed activities")
    highlights: Optional[List[str]] = Field(None, description="Fun/notable moments")
    parent_notes: Optional[str] = Field(None, description="Parent observations")
    
    class Config:
        from_attributes = True


class ChildSummarySchema(BaseModel):
    summary_id: str = Field(..., description="Unique summary identifier")
    child_id: int = Field(..., description="Child ID")
    week_of: datetime = Field(..., description="Week starting date")
    completed_goals: Optional[List[str]] = Field(None, description="Goals achieved this week")
    fun_moments: Optional[List[str]] = Field(None, description="Fun/positive moments")
    growth_notes: Optional[str] = Field(None, description="User observations about growth")
    next_week_focus: Optional[List[str]] = Field(None, description="Focus areas for next week")
    
    class Config:
        from_attributes = True


class ChildEducationResponse(BaseModel):
    total_children: int = Field(..., description="Total number of child profiles")
    active_plans: int = Field(..., description="Number of active learning plans")
    this_week_logs: int = Field(..., description="Education logs this week")
    recent_highlights: Optional[List[str]] = Field(None, description="Recent fun moments across all children")
