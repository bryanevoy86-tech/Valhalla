from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class LegacyPerformanceBase(BaseModel):
    legacy_code: str
    display_name: str
    period: str = "month"
    period_label: str
    gross_income: float = 0.0
    net_profit: float = 0.0
    reinvestment: float = 0.0
    fun_fund: float = 0.0
    deals_closed: int = 0
    brRRR_units: int = 0
    flips: int = 0
    wholesale_deals: int = 0
    risk_flag: bool = False
    risk_note: Optional[str] = None
    status: Optional[str] = "normal"


class LegacyPerformanceCreate(LegacyPerformanceBase):
    pass


class LegacyPerformanceOut(LegacyPerformanceBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True
