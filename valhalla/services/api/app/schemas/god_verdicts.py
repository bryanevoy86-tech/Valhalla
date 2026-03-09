from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class GodVerdictCreate(BaseModel):
    case_id: UUID

    trigger: Optional[str] = None

    heimdall_summary: Optional[str] = None
    heimdall_recommendation: Optional[dict[str, Any]] = None
    heimdall_confidence: Optional[str] = None

    loki_summary: Optional[str] = None
    loki_recommendation: Optional[dict[str, Any]] = None
    loki_confidence: Optional[str] = None

    consensus: Optional[str] = None
    risk_level: Optional[str] = None

    notes: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class GodVerdictRead(BaseModel):
    id: UUID
    created_at: datetime

    case_id: UUID
    trigger: Optional[str] = None

    heimdall_summary: Optional[str] = None
    heimdall_recommendation: Optional[dict[str, Any]] = None
    heimdall_confidence: Optional[str] = None

    loki_summary: Optional[str] = None
    loki_recommendation: Optional[dict[str, Any]] = None
    loki_confidence: Optional[str] = None

    consensus: Optional[str] = None
    risk_level: Optional[str] = None

    notes: Optional[str] = None
    metadata: Optional[dict[str, Any]] = Field(default=None, validation_alias="metadata_json")

    model_config = {"from_attributes": True}
