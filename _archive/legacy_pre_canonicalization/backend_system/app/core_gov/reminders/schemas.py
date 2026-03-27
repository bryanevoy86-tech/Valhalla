from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


Status = Literal["active", "done", "archived"]
Priority = Literal["low", "normal", "high", "critical"]


class ReminderCreate(BaseModel):
    title: str
    due_date: str                   # "YYYY-MM-DD"
    status: Status = "active"
    priority: Priority = "normal"
    source: str = "manual"          # manual / budget / shopping / system
    ref: str = ""                   # optional stable ref for dedupe
    notes: str = ""
    meta: Dict[str, Any] = Field(default_factory=dict)


class ReminderRecord(BaseModel):
    id: str
    title: str
    due_date: str
    status: Status
    priority: Priority
    source: str
    ref: str = ""
    notes: str = ""
    meta: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class ReminderListResponse(BaseModel):
    items: List[ReminderRecord]


class GenerateFromBudgetRequest(BaseModel):
    lookahead_days: int = 30
    lead_days: int = 3
    max_create: int = 50


class GenerateFromShoppingRequest(BaseModel):
    default_lead_days: int = 2
    max_create: int = 50
