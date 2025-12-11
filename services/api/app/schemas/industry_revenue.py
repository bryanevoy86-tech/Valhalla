"""PACK 84: Industry Engine - Revenue Simulator Schemas"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict


class RevenueSimBase(BaseModel):
    industry_id: int
    assumptions_payload: str
    low_estimate: float
    mid_estimate: float
    high_estimate: float


class RevenueSimCreate(RevenueSimBase):
    pass


class RevenueSimOut(RevenueSimBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
