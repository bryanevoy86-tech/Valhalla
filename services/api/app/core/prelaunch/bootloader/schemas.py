"""PACK-CORE-PRELAUNCH-01: Bootloader - Schemas"""

from datetime import datetime
from typing import List
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BootStep(BaseModel):
    name: str
    status: str
    message: str | None = None


class BootLogRead(BaseModel):
    id: UUID
    run_at: datetime
    status: str
    steps: List[BootStep]

    model_config = ConfigDict(from_attributes=True)
