from __future__ import annotations
from datetime import datetime
from typing import Any, Optional
from uuid import UUID
from pydantic import BaseModel


class GodSyncRecordBase(BaseModel):
    subject_type: str
    subject_reference: Optional[str] = None
    heimdall_payload: Optional[dict[str, Any]] = None
    loki_payload: Optional[dict[str, Any]] = None


class GodSyncRecordCreate(GodSyncRecordBase):
    pass


class GodSyncRecordRead(GodSyncRecordBase):
    id: UUID
    created_at: datetime
    sync_status: str
    conflict_summary: Optional[str] = None
    forwarded_case_id: Optional[UUID] = None

    model_config = {"from_attributes": True}
