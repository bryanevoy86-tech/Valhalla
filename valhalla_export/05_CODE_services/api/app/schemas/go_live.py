from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class GoLiveStateOut(BaseModel):
    go_live_enabled: bool
    kill_switch_engaged: bool
    changed_by: Optional[str] = None
    reason: Optional[str] = None
    updated_at: datetime

    class Config:
        from_attributes = True


class GoLiveToggleIn(BaseModel):
    changed_by: str = Field(..., min_length=1, max_length=200)
    reason: Optional[str] = Field(None, max_length=1000)


class GoLiveChecklistOut(BaseModel):
    ok: bool
    required: Dict[str, Any]
    warnings: Dict[str, Any]
