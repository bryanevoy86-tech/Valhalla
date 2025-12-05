# services/api/app/schemas/pro_retainer.py

from __future__ import annotations

from datetime import date
from typing import Optional
from pydantic import BaseModel, Field


class RetainerIn(BaseModel):
    professional_id: int
    name: str = Field(..., description="Name of the retainer agreement")
    monthly_hours_included: float = Field(..., description="Hours included per month")
    hourly_rate: Optional[float] = Field(None, description="Rate for overage hours")
    renewal_date: date = Field(..., description="Next renewal date")


class RetainerOut(RetainerIn):
    id: int
    hours_used: float
    is_active: bool

    class Config:
        from_attributes = True


class HoursLogRequest(BaseModel):
    hours: float = Field(..., description="Number of hours to log", gt=0)
