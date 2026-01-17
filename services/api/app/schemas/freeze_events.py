# services/api/app/schemas/freeze_events.py

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class FreezeEventBase(BaseModel):
    source: Optional[str] = Field(
        default=None,
        description="What triggered the freeze (scheduler, policy, manual, etc.).",
    )
    event_type: Optional[str] = Field(
        default=None,
        description="Short code for the freeze reason (e.g. 'liquidity', 'policy_violation').",
    )
    reason: Optional[str] = Field(
        default=None,
        description="Human-readable reason for the freeze.",
    )
    severity: Optional[str] = Field(
        default=None,
        description="Severity level (info/warn/critical).",
    )
    payload: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional structured data captured at freeze time.",
    )
    resolved_at: Optional[datetime] = Field(
        default=None,
        description="When (if) this freeze event was resolved.",
    )
    resolved_by: Optional[str] = Field(
        default=None,
        description="Who or what resolved the freeze.",
    )
    notes: Optional[str] = Field(
        default=None,
        description="Free-form notes for extra context.",
    )


class FreezeEventRead(FreezeEventBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class FreezeEventList(BaseModel):
    total: int
    items: List[FreezeEventRead]
