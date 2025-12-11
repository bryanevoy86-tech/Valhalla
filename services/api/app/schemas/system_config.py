"""
PACK TZ: Config & Environment Registry Schemas
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class SystemConfigSet(BaseModel):
    key: str
    value: Optional[str] = None
    description: Optional[str] = None
    mutable: bool = True


class SystemConfigOut(SystemConfigSet):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SystemConfigList(BaseModel):
    total: int
    items: List[SystemConfigOut]
