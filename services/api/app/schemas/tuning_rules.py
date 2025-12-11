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
