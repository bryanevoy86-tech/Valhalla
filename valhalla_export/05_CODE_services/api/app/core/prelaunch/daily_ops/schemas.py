"""PACK-CORE-PRELAUNCH-01: Daily Ops - Schemas"""

from datetime import date, datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DailySnapshotBase(BaseModel):
    snapshot_date: date
    financial_summary: Optional[dict[str, Any]] = None
    risk_summary: Optional[dict[str, Any]] = None
    tasks_today: Optional[list[dict[str, Any]]] = None
    alerts_summary: Optional[dict[str, Any]] = None
    notes: Optional[dict[str, Any]] = None


class DailySnapshotRead(DailySnapshotBase):
    id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NightlySnapshotBase(BaseModel):
    snapshot_date: date
    completed_tasks: Optional[list[dict[str, Any]]] = None
    missed_tasks: Optional[list[dict[str, Any]]] = None
    projection_changes: Optional[dict[str, Any]] = None
    risk_changes: Optional[dict[str, Any]] = None
    notes: Optional[dict[str, Any]] = None


class NightlySnapshotRead(NightlySnapshotBase):
    id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
