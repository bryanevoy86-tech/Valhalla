# services/api/app/schemas/audit_event.py

from __future__ import annotations

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class AuditEventBase(BaseModel):
    deal_id: Optional[int] = None
    professional_id: Optional[int] = None
    code: str = Field(..., description="Event code: MISSING_SIGNED_CONTRACT, etc.")
    severity: str = Field(default="warning", description="Severity: info, warning, critical")
    message: str = Field(..., description="Human-readable issue description")


class AuditEventOut(AuditEventBase):
    id: int
    is_resolved: bool
    created_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True
