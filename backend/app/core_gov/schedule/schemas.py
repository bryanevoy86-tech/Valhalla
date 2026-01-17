from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


Kind = Literal["task", "event", "reminder"]
Status = Literal["open", "done", "canceled"]
Priority = Literal["A", "B", "C", "D"]


class ScheduleCreate(BaseModel):
    title: str
    kind: Kind = "task"
    due_date: str                 # YYYY-MM-DD
    due_time: str = ""            # HH:MM (optional)
    timezone: str = "America/Toronto"
    priority: Priority = "B"
    status: Status = "open"
    link_type: str = ""           # obligation/flow/replacement/deal/etc.
    link_id: str = ""
    est_cost: float = 0.0
    currency: str = "CAD"
    notes: str = ""
    tags: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)


class ScheduleRecord(BaseModel):
    id: str
    title: str
    kind: Kind
    due_date: str
    due_time: str = ""
    timezone: str
    priority: Priority
    status: Status
    link_type: str = ""
    link_id: str = ""
    est_cost: float = 0.0
    currency: str = "CAD"
    notes: str = ""
    tags: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class ScheduleListResponse(BaseModel):
    items: List[ScheduleRecord]
