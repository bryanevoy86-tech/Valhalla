"""
PACK L0-09: Strategic Event Schemas
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class StrategicEventBase(BaseModel):
    """Base schema for strategic events."""
    source: str = Field(..., description="Module that generated the event")
    category: str = Field(..., description="mode_change, decision, deal, rule, crisis, win, etc.")
    label: str = Field(..., description="Human-readable event label")
    payload: Optional[Dict[str, Any]] = Field(default=None, description="Structured event data")
    importance_score: float = Field(default=0.5, ge=0.0, le=1.0, description="0.0 to 1.0")


class StrategicEventCreate(StrategicEventBase):
    """Schema for creating a strategic event."""
    pass


class StrategicEventOut(StrategicEventBase):
    """Schema for outputting a strategic event."""
    id: int
    tenant_id: str
    timestamp: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StrategicEventList(BaseModel):
    """Paginated list of strategic events."""
    total: int
    items: List[StrategicEventOut]

    class Config:
        from_attributes = True


class StrategicEventList(BaseModel):
    total: int
    items: List[StrategicEventOut]
