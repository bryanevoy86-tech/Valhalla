"""
PACK L0-09: Tuning Rules Schemas
"""

from datetime import datetime
from typing import Optional, Any, Dict, List
from pydantic import BaseModel, Field, ConfigDict


class TuningRuleBase(BaseModel):
    """Base schema for tuning rules."""
    name: str = Field(..., description="Rule name, e.g. 'max_deal_value'")
    description: Optional[str] = None
    rule_type: str = Field(default="threshold", description="threshold, toggle, percentage, choice, etc.")
    config: Dict[str, Any] = Field(..., description="Rule configuration")
    active: bool = Field(default=True)


class TuningRuleCreate(TuningRuleBase):
    """Schema for creating a tuning rule."""
    pass


class TuningRuleUpdate(BaseModel):
    """Schema for updating a tuning rule."""
    name: Optional[str] = None
    description: Optional[str] = None
    rule_type: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    active: Optional[bool] = None


class TuningRuleOut(TuningRuleBase):
    """Schema for outputting a tuning rule."""
    id: int
    tenant_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TuningRuleList(BaseModel):
    """Paginated list of tuning rules."""
    total: int
    items: List[TuningRuleOut]


class ProfileSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")
    aggression: int = Field(50, ge=0, le=100)
    risk_tolerance: int = Field(50, ge=0, le=100)
    safety_bias: int = Field(70, ge=0, le=100)
    growth_bias: int = Field(70, ge=0, le=100)
    stability_bias: int = Field(60, ge=0, le=100)
    weights: Optional[Dict[str, Any]] = None


class ProfileConstraintSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")
    profile_id: int = Field(gt=0, strict=True)
    rules: Optional[Dict[str, Any]] = None
