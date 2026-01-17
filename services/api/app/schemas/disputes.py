from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel


class DisputeCreate(BaseModel):
    case_id: UUID

    human_role: Optional[str] = None
    human_specialist_id: Optional[UUID] = None

    topic: Optional[str] = None
    description: Optional[str] = None

    human_position: Optional[dict[str, Any]] = None
    heimdall_position: Optional[dict[str, Any]] = None
    loki_position: Optional[dict[str, Any]] = None


class DisputeUpdate(BaseModel):
    status: Optional[str] = None
    human_position: Optional[dict[str, Any]] = None
    heimdall_position: Optional[dict[str, Any]] = None
    loki_position: Optional[dict[str, Any]] = None
    resolution_summary: Optional[str] = None
    resolution_metadata: Optional[dict[str, Any]] = None


class DisputeRead(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: datetime

    case_id: UUID

    human_role: Optional[str] = None
    human_specialist_id: Optional[UUID] = None

    topic: Optional[str] = None
    description: Optional[str] = None

    human_position: Optional[dict[str, Any]] = None
    heimdall_position: Optional[dict[str, Any]] = None
    loki_position: Optional[dict[str, Any]] = None

    status: str
    resolution_summary: Optional[str] = None
    resolution_metadata: Optional[dict[str, Any]] = None

    model_config = {"from_attributes": True}
