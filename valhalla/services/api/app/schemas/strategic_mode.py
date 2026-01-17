"""
PACK CI7: Strategic Mode Engine Schemas
"""

from datetime import datetime
from typing import Optional, Any, Dict, List
from pydantic import BaseModel


class StrategicModeIn(BaseModel):
    name: str
    description: Optional[str] = None
    tuning_profile_name: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    active: bool = True


class StrategicModeOut(StrategicModeIn):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class StrategicModeList(BaseModel):
    total: int
    items: List[StrategicModeOut]


class ActiveModeSet(BaseModel):
    mode_name: str
    reason: Optional[str] = None


class ActiveModeOut(BaseModel):
    id: int
    mode_name: str
    changed_at: datetime
    reason: Optional[str]

    class Config:
        from_attributes = True
