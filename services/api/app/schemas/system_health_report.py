from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class SystemHealthReportBase(BaseModel):
    period_label: str
    errors_count: int = 0
    critical_errors: int = 0
    failed_automations: int = 0
    unresolved_compliance_signals: int = 0
    all_green: bool = False
    summary: Optional[str] = None
    notes: Optional[str] = None


class SystemHealthReportCreate(SystemHealthReportBase):
    run_at: Optional[datetime] = None


class SystemHealthReportOut(SystemHealthReportBase):
    id: int
    run_at: datetime

    class Config:
        orm_mode = True
