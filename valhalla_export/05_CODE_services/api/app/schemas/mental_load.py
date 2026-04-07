"""
PACK SN: Mental Load Offloading Engine
Pydantic schemas for brain externalization and task management
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class MentalLoadEntrySchema(BaseModel):
    entry_id: str = Field(..., description="Unique entry identifier")
    category: str = Field(..., description="task, worry, reminder, idea, future, or household")
    description: str = Field(..., description="What's on your mind")
    urgency_level: Optional[int] = Field(None, description="1-5 user-defined urgency")
    emotional_weight: Optional[int] = Field(None, description="1-10 user-defined weight (not interpreted)")
    action_required: Optional[bool] = Field(False, description="Does this need action?")
    cleared: Optional[bool] = Field(False, description="Has this been cleared?")
    user_notes: Optional[str] = Field(None, description="Any additional notes")
    
    class Config:
        from_attributes = True


class DailyLoadSummarySchema(BaseModel):
    summary_id: str = Field(..., description="Unique summary identifier")
    date: datetime = Field(..., description="Date of summary")
    total_items: int = Field(..., description="Total items in load")
    urgent_items: Optional[List[str]] = Field(None, description="High urgency items")
    action_items: Optional[List[str]] = Field(None, description="Items requiring action today")
    delegated_items: Optional[List[str]] = Field(None, description="Items delegated to others")
    cleared_items: Optional[List[str]] = Field(None, description="Items cleared today")
    waiting_items: Optional[List[str]] = Field(None, description="Items awaiting response")
    parked_items: Optional[List[str]] = Field(None, description="Items deferred to later")
    notes: Optional[str] = Field(None, description="Daily summary notes")
    
    class Config:
        from_attributes = True


class LoadOffloadWorkflowSchema(BaseModel):
    workflow_id: str = Field(..., description="Unique workflow identifier")
    brain_dump: Optional[str] = Field(None, description="Raw brain dump input")
    processed_count: int = Field(default=0, description="Items processed")
    categorized_items: Optional[List[Dict[str, Any]]] = Field(None, description="Items categorized")
    workflow_stage: str = Field(default="intake", description="intake, categorizing, or ready")
    
    class Config:
        from_attributes = True


class MentalLoadResponse(BaseModel):
    total_load_items: int = Field(..., description="Total items tracked")
    urgent_count: int = Field(..., description="Number of urgent items")
    action_count: int = Field(..., description="Items requiring action")
    cleared_today: int = Field(..., description="Items cleared today")
    cognitive_pressure: float = Field(..., description="Overall cognitive load (0-100)")
    focus_areas: Optional[List[str]] = Field(None, description="Top items demanding attention")
