"""
PACK UE: Maintenance Window & Freeze Switch Schemas
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class MaintenanceWindowCreate(BaseModel):
    starts_at: datetime
    ends_at: datetime
    description: Optional[str] = None
    active: bool = True


class MaintenanceWindowOut(MaintenanceWindowCreate):
    id: int

    class Config:
        from_attributes = True


class MaintenanceWindowList(BaseModel):
    total: int
    items: List[MaintenanceWindowOut]


class MaintenanceStateOut(BaseModel):
    mode: str
    reason: Optional[str]
    updated_at: datetime
