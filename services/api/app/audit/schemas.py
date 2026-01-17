from pydantic import BaseModel
from typing import Optional, Any, Dict
from datetime import datetime


class AuditEventCreate(BaseModel):
    actor: str
    action: str
    target: Optional[str] = None
    result: str
    ip: Optional[str] = None
    user_agent: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None


class AuditEventResponse(AuditEventCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
