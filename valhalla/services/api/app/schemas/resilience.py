"""
PACK TD: Resilience & Recovery Planner Schemas
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class RecoveryActionBase(BaseModel):
    description: str = Field(..., description="Action description")
    order: Optional[int] = Field(None, description="Step order in sequence")


class RecoveryActionCreate(RecoveryActionBase):
    pass


class RecoveryActionOut(RecoveryActionBase):
    id: int
    completed: bool
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RecoveryPlanBase(BaseModel):
    name: str = Field(..., description="Recovery plan name")
    goal: Optional[str] = Field(None, description="What success looks like")


class RecoveryPlanCreate(RecoveryPlanBase):
    setback_id: int = Field(..., description="Setback this plan addresses")


class RecoveryPlanOut(RecoveryPlanBase):
    id: int
    status: str = Field(..., description="active, paused, or completed")
    created_at: datetime
    actions: List[RecoveryActionOut] = []

    class Config:
        from_attributes = True


class SetbackEventBase(BaseModel):
    title: str = Field(..., description="What happened")
    category: Optional[str] = Field(None, description="financial, family, health, system, etc.")
    description: Optional[str] = Field(None, description="Details about the setback")
    severity: Optional[int] = Field(None, ge=1, le=5, description="1–5 severity scale")


class SetbackEventCreate(SetbackEventBase):
    pass


class SetbackEventOut(SetbackEventBase):
    id: int
    date: datetime
    resolved: bool
    recovery_plans: List[RecoveryPlanOut] = []

    class Config:
        from_attributes = True
