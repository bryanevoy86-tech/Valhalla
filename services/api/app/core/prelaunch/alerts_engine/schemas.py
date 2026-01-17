"""PACK-CORE-PRELAUNCH-01: Alerts Engine - Schemas"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from .models import AlertLevel, AlertDomain, AlertStatus


class AlertBase(BaseModel):
    level: AlertLevel
    domain: AlertDomain
    title: str
    message: str
    alert_metadata: Optional[dict[str, Any]] = None
    source: str


class AlertCreate(AlertBase):
    pass


class AlertUpdate(BaseModel):
    status: Optional[AlertStatus] = None
    resolved_at: Optional[datetime] = None


class AlertRead(AlertBase):
    id: UUID
    status: AlertStatus
    created_at: datetime
    resolved_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
