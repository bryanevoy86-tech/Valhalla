"""
PACK L0-09: Strategic Decision Schemas
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict


class StrategicDecisionBase(BaseModel):
    """Base schema for strategic decisions."""
    input_context: Dict[str, Any] = Field(..., description="Context that led to this decision")
    recommendation: Dict[str, Any] = Field(..., description="The proposed action and rationale")
    confidence_score: float = Field(default=0.5, ge=0.0, le=1.0, description="0.0 to 1.0")
    risk_level: str = Field(default="MEDIUM", description="LOW, MEDIUM, HIGH, CRITICAL")


class StrategicDecisionCreate(StrategicDecisionBase):
    """Schema for creating a strategic decision."""
    mode_id: Optional[int] = Field(default=None, description="Strategic mode ID")


class StrategicDecisionStatusUpdate(BaseModel):
    """Schema for updating decision status."""
    status: str = Field(..., description="APPROVED, REJECTED, EXECUTED, WITHDRAWN")
    reviewer: Optional[str] = Field(default=None, description="User ID or system identifier")


class StrategicDecisionOut(StrategicDecisionBase):
    """Schema for outputting a strategic decision."""
    id: int
    tenant_id: str
    mode_id: Optional[int] = None
    timestamp: datetime
    status: str
    reviewer: Optional[str] = None
    created_at: datetime
    reviewed_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class StrategicDecisionList(BaseModel):
    """Paginated list of strategic decisions."""
    total: int
    items: List[StrategicDecisionOut]

    class Config:
        from_attributes = True
