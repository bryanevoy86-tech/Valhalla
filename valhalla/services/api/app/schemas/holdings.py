"""
PACK Z: Global Holdings Engine Schemas
"""

from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field


class HoldingCreate(BaseModel):
    asset_type: str = Field(..., description="property, resort, policy, trust_interest, etc.")
    internal_ref: Optional[str] = None
    jurisdiction: Optional[str] = None
    entity_name: Optional[str] = None
    entity_id: Optional[str] = None
    label: Optional[str] = None
    notes: Optional[str] = None
    value_estimate: Optional[float] = None
    currency: Optional[str] = "USD"


class HoldingUpdate(BaseModel):
    jurisdiction: Optional[str] = None
    entity_name: Optional[str] = None
    entity_id: Optional[str] = None
    label: Optional[str] = None
    notes: Optional[str] = None
    value_estimate: Optional[float] = None
    currency: Optional[str] = None
    is_active: Optional[bool] = None


class HoldingOut(BaseModel):
    id: int
    asset_type: str
    internal_ref: Optional[str]
    jurisdiction: Optional[str]
    entity_name: Optional[str]
    entity_id: Optional[str]
    label: Optional[str]
    notes: Optional[str]
    value_estimate: Optional[float]
    currency: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class HoldingsSummary(BaseModel):
    total_value: float
    by_asset_type: Dict[str, float]
    by_jurisdiction: Dict[str, float]
