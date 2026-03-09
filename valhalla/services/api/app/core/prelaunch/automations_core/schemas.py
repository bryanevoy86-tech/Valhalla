"""PACK-CORE-PRELAUNCH-01: Automations Core - Schemas"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AutomationJobRead(BaseModel):
    id: UUID
    code: str
    name: str
    schedule: Optional[str] = None
    enabled: bool
    last_run_at: Optional[datetime] = None
    last_status: Optional[str] = None
    last_result: Optional[dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
