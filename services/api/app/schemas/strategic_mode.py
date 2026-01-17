"""
PACK L0-09: Strategic Mode Schemas
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict


class StrategicModeBase(BaseModel):
    """Base schema for strategic mode."""
    name: str
    description: Optional[str] = None
    parameters: Dict[str, Any] = {}
    active: bool = False


class StrategicModeCreate(StrategicModeBase):
    """Schema for creating a strategic mode."""
    pass


class StrategicModeUpdate(BaseModel):
    """Schema for updating a strategic mode."""
    name: Optional[str] = None
    description: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    active: Optional[bool] = None


class StrategicModeOut(StrategicModeBase):
    """Schema for outputting a strategic mode."""
    id: int
    tenant_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StrategicModeList(BaseModel):
    """Paginated list of strategic modes."""
    total: int
    items: List[StrategicModeOut]
    reason: Optional[str]

    class Config:
        from_attributes = True
