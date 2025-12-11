"""PACK-PRELAUNCH-09: Behavior Engine Schemas"""
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BehaviorBase(BaseModel):
    name: str
    role: Optional[str] = None
    public_data: Optional[dict[str, Any]] = None
    alignment_score: float
    risk_score: float
    recommended_style: Optional[dict[str, Any]] = None


class BehaviorCreate(BehaviorBase):
    pass


class BehaviorUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    public_data: Optional[dict[str, Any]] = None
    alignment_score: Optional[float] = None
    risk_score: Optional[float] = None
    recommended_style: Optional[dict[str, Any]] = None


class BehaviorRead(BehaviorBase):
    id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
