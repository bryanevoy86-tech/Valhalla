from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


Level = Literal["info", "warn", "error"]
EventType = Literal[
    "system",
    "cone_decision",
    "mode_switch",
    "export_backup",
    "legal_flag",
    "comms_sent",
    "credit_update",
    "trust_update",
    "custom",
]


class AuditEventCreate(BaseModel):
    event_type: EventType = "custom"
    level: Level = "info"
    message: str
    actor: str = "api"
    ref_type: str = ""   # "deal", "entity", "draft", etc.
    ref_id: str = ""
    meta: Dict[str, Any] = Field(default_factory=dict)


class AuditEventRecord(BaseModel):
    id: str
    event_type: str
    level: str
    message: str
    actor: str
    ref_type: str = ""
    ref_id: str = ""
    meta: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class AuditListResponse(BaseModel):
    items: List[AuditEventRecord]
