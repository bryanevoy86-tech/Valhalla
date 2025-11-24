from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class EmpireSnapshotCreate(BaseModel):
    label: str
    snapshot_type: Optional[str] = "manual"
    summary_json: str
    notes: Optional[str] = None


class EmpireSnapshotOut(EmpireSnapshotCreate):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True
