from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class SystemHealthSnapshotBase(BaseModel):
    scope: str
    scope_code: Optional[str] = None
    health_score: float = 1.0
    income_status: str = "green"
    liquidity_status: str = "green"
    deal_flow_status: str = "green"
    compliance_status: str = "green"
    ai_status: str = "green"
    summary: Optional[str] = None
    details_json: Optional[str] = None


class SystemHealthSnapshotCreate(SystemHealthSnapshotBase):
    pass


class SystemHealthSnapshotOut(SystemHealthSnapshotBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True
