"""
Schemas for audit log.
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AuditLogOut(BaseModel):
    id: int
    deal_id: Optional[int] = None
    event_type: str
    event_source: str
    message: str
    metadata: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
