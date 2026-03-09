from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class KpiMetricBase(BaseModel):
    name: str
    scope: Optional[str] = "empire"
    scope_ref: Optional[str] = None
    period: Optional[str] = "month"
    period_label: str
    value: float = 0.0
    currency: Optional[str] = "CAD"


class KpiMetricCreate(KpiMetricBase):
    pass


class KpiMetricUpdate(BaseModel):
    value: Optional[float]
    currency: Optional[str]


class KpiMetricOut(KpiMetricBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True
