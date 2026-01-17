from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class EmpireSnapshotBase(BaseModel):
    # New Pack 110 metric fields
    period: str = "month"
    period_label: Optional[str] = None
    gross_income: float = 0.0
    taxes_reserved: float = 0.0
    reinvestment: float = 0.0
    fun_fund: float = 0.0
    legacy_count: int = 0
    active_zones: int = 0
    brRRR_count: int = 0
    flip_count: int = 0
    wholesale_count: int = 0
    resort_count: int = 0
    shield_mode_active: bool = False
    black_ice_armed: bool = False
    bahamas_ready: bool = False

    # Backward compatibility fields (optional now)
    label: Optional[str] = None
    snapshot_type: Optional[str] = "manual"
    summary_json: Optional[str] = None
    notes: Optional[str] = None


class EmpireSnapshotCreate(EmpireSnapshotBase):
    pass


class EmpireSnapshotOut(EmpireSnapshotBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True
