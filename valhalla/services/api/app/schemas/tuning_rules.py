"""
PACK CI5: Heimdall Tuning Ruleset Schemas
"""

from datetime import datetime
from typing import Optional, Any, Dict, List
from pydantic import BaseModel, Field


class TuningProfileIn(BaseModel):
    name: str = Field(..., description="Profile name, e.g. 'default', 'war_mode'")
    description: Optional[str] = None

    aggression: int = Field(50, ge=0, le=100)
    risk_tolerance: int = Field(50, ge=0, le=100)
    safety_bias: int = Field(70, ge=0, le=100)
    growth_bias: int = Field(70, ge=0, le=100)
    stability_bias: int = Field(60, ge=0, le=100)

    weights: Optional[Dict[str, Any]] = None
    active: bool = True


class TuningProfileOut(TuningProfileIn):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TuningConstraintIn(BaseModel):
    profile_id: int
    key: str
    description: str
    rules: Optional[Dict[str, Any]] = None


class TuningConstraintOut(TuningConstraintIn):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class TuningProfileList(BaseModel):
    total: int
    items: List[TuningProfileOut]


class TuningConstraintList(BaseModel):
    total: int
    items: List[TuningConstraintOut]
