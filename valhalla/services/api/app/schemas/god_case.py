from __future__ import annotations

from typing import Any, Optional
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field


class GodCaseBase(BaseModel):
    title: str = Field(..., max_length=255)
    source_type: str = Field("generic", max_length=50)
    status: str = Field("open", max_length=50)
    payload: dict[str, Any]


class GodCaseCreate(GodCaseBase):
    heimdall_output: Optional[dict[str, Any]] = None
    loki_output: Optional[dict[str, Any]] = None
    arbitration_output: Optional[dict[str, Any]] = None


class GodCaseUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    heimdall_output: Optional[dict[str, Any]] = None
    loki_output: Optional[dict[str, Any]] = None
    arbitration_output: Optional[dict[str, Any]] = None
    needs_rescan: Optional[bool] = None
    rescan_count: Optional[int] = None
    last_rescan_at: Optional[datetime] = None
    last_specialist_feedback_at: Optional[datetime] = None


class GodCaseRead(GodCaseBase):
    id: UUID
    heimdall_output: Optional[dict[str, Any]] = None
    loki_output: Optional[dict[str, Any]] = None
    arbitration_output: Optional[dict[str, Any]] = None
    needs_rescan: bool
    rescan_count: int
    last_rescan_at: Optional[datetime] = None
    last_specialist_feedback_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
