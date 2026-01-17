"""
Pydantic v2 schemas for PACK ST, SU, SV

Request/response models with validation.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ============================================================================
# PACK ST: Financial Stress Early Warning Engine Schemas
# ============================================================================

class FinancialIndicatorCreate(BaseModel):
    """Create a financial indicator."""
    name: str = Field(..., min_length=1, max_length=255)
    category: str = Field(..., pattern="^(income|expenses|cashflow|savings)$")
    threshold_type: str = Field(..., pattern="^(above|below)$")
    threshold_value: float
    notes: Optional[str] = None


class FinancialIndicatorUpdate(BaseModel):
    """Update a financial indicator."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    category: Optional[str] = Field(None, pattern="^(income|expenses|cashflow|savings)$")
    threshold_type: Optional[str] = Field(None, pattern="^(above|below)$")
    threshold_value: Optional[float] = None
    notes: Optional[str] = None


class FinancialIndicatorResponse(FinancialIndicatorCreate):
    """Response model for financial indicator."""
    id: int
    indicator_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FinancialStressEventCreate(BaseModel):
    """Create a financial stress event."""
    indicator_id: int
    date: datetime
    value_at_trigger: float
    description: str = Field(..., min_length=1)
    resolved: Optional[bool] = False
    notes: Optional[str] = None


class FinancialStressEventUpdate(BaseModel):
    """Update a financial stress event."""
    resolved: Optional[bool] = None
    notes: Optional[str] = None


class FinancialStressEventResponse(FinancialStressEventCreate):
    """Response model for financial stress event."""
    id: int
    event_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FinancialStressSummaryCreate(BaseModel):
    """Create a financial stress summary."""
    month: str = Field(..., pattern="^\\d{4}-\\d{2}$")  # YYYY-MM
    triggered_indicators: Optional[List[str]] = None
    patterns: Optional[List[str]] = None
    recommendations_to_self: Optional[List[str]] = None
    notes: Optional[str] = None


class FinancialStressSummaryUpdate(BaseModel):
    """Update a financial stress summary."""
    triggered_indicators: Optional[List[str]] = None
    patterns: Optional[List[str]] = None
    recommendations_to_self: Optional[List[str]] = None
    notes: Optional[str] = None


class FinancialStressSummaryResponse(FinancialStressSummaryCreate):
    """Response model for financial stress summary."""
    id: int
    summary_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# PACK SU: Personal Safety & Risk Mitigation Planner Schemas
# ============================================================================

class SafetyCategoryCreate(BaseModel):
    """Create a safety category."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class SafetyCategoryUpdate(BaseModel):
    """Update a safety category."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None


class SafetyCategoryResponse(SafetyCategoryCreate):
    """Response model for safety category."""
    id: int
    category_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SafetyChecklistCreate(BaseModel):
    """Create a safety checklist item."""
    category_id: int
    item: str = Field(..., min_length=1, max_length=255)
    frequency: str = Field(..., pattern="^(daily|weekly|before_travel|as_needed)$")
    notes: Optional[str] = None
    status: Optional[str] = Field("active", pattern="^(active|retired)$")


class SafetyChecklistUpdate(BaseModel):
    """Update a safety checklist item."""
    item: Optional[str] = Field(None, min_length=1, max_length=255)
    frequency: Optional[str] = Field(None, pattern="^(daily|weekly|before_travel|as_needed)$")
    notes: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(active|retired)$")


class SafetyChecklistResponse(SafetyChecklistCreate):
    """Response model for safety checklist."""
    id: int
    checklist_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SafetyStep(BaseModel):
    """Step in a safety plan."""
    step: str
    order: int


class SafetyPlanCreate(BaseModel):
    """Create a safety plan."""
    situation: str = Field(..., min_length=1, max_length=255)
    steps: Optional[List[SafetyStep]] = None
    notes: Optional[str] = None


class SafetyPlanUpdate(BaseModel):
    """Update a safety plan."""
    situation: Optional[str] = Field(None, min_length=1, max_length=255)
    steps: Optional[List[SafetyStep]] = None
    notes: Optional[str] = None


class SafetyPlanResponse(SafetyPlanCreate):
    """Response model for safety plan."""
    id: int
    plan_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SafetyEventLogCreate(BaseModel):
    """Create a safety event log."""
    date: datetime
    category_id: int
    event: str = Field(..., min_length=1)
    resolution_notes: Optional[str] = None


class SafetyEventLogResponse(SafetyEventLogCreate):
    """Response model for safety event log."""
    id: int
    log_id: str
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# PACK SV: Empire Growth Navigator Schemas
# ============================================================================

class EmpireGoalCreate(BaseModel):
    """Create an empire goal."""
    name: str = Field(..., min_length=1, max_length=255)
    category: str = Field(..., pattern="^(finance|business|family|skills|real_estate|automation)$")
    description: Optional[str] = None
    timeframe: str = Field(..., pattern="^(short_term|mid_term|long_term)$")
    status: Optional[str] = Field("not_started", pattern="^(not_started|in_progress|completed|paused)$")
    notes: Optional[str] = None


class EmpireGoalUpdate(BaseModel):
    """Update an empire goal."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    category: Optional[str] = Field(None, pattern="^(finance|business|family|skills|real_estate|automation)$")
    description: Optional[str] = None
    timeframe: Optional[str] = Field(None, pattern="^(short_term|mid_term|long_term)$")
    status: Optional[str] = Field(None, pattern="^(not_started|in_progress|completed|paused)$")
    notes: Optional[str] = None


class EmpireGoalResponse(EmpireGoalCreate):
    """Response model for empire goal."""
    id: int
    goal_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GoalMilestoneCreate(BaseModel):
    """Create a goal milestone."""
    goal_id: int
    description: str = Field(..., min_length=1)
    due_date: Optional[datetime] = None
    progress: Optional[float] = Field(0.0, ge=0.0, le=1.0)
    notes: Optional[str] = None


class GoalMilestoneUpdate(BaseModel):
    """Update a goal milestone."""
    description: Optional[str] = Field(None, min_length=1)
    due_date: Optional[datetime] = None
    progress: Optional[float] = Field(None, ge=0.0, le=1.0)
    notes: Optional[str] = None


class GoalMilestoneResponse(GoalMilestoneCreate):
    """Response model for goal milestone."""
    id: int
    milestone_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ActionStepCreate(BaseModel):
    """Create an action step."""
    milestone_id: int
    description: str = Field(..., min_length=1)
    priority: Optional[int] = Field(1, ge=1)
    status: Optional[str] = Field("pending", pattern="^(pending|in_progress|done)$")
    notes: Optional[str] = None


class ActionStepUpdate(BaseModel):
    """Update an action step."""
    description: Optional[str] = Field(None, min_length=1)
    priority: Optional[int] = Field(None, ge=1)
    status: Optional[str] = Field(None, pattern="^(pending|in_progress|done)$")
    notes: Optional[str] = None


class ActionStepResponse(ActionStepCreate):
    """Response model for action step."""
    id: int
    step_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
