"""
PACK TV: System Log & Audit Trail Schemas
"""

from datetime import datetime
from typing import Optional, Any, Dict, List
from pydantic import BaseModel, ConfigDict


class SystemLogCreate(BaseModel):
    level: str = "INFO"
    category: str = "general"
    message: str
    correlation_id: Optional[str] = None
    user_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class SystemLogOut(BaseModel):
    id: int
    timestamp: datetime
    level: str
    category: str
    message: str
    correlation_id: Optional[str]
    user_id: Optional[str]
    context: Optional[Dict[str, Any]]

    model_config = ConfigDict(from_attributes=True)


class SystemLogList(BaseModel):
    total: int
    items: List[SystemLogOut]

    model_config = ConfigDict(from_attributes=True)
