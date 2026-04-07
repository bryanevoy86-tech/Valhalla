"""PACK-CORE-PRELAUNCH-01: Unified Log - Schemas"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from .models import EventType


class SystemEventCreate(BaseModel):
    event_type: EventType
    source: str
    message: str
    data: Optional[dict[str, Any]] = None
    correlation_id: Optional[str] = None


class SystemEventRead(SystemEventCreate):
    id: UUID
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
