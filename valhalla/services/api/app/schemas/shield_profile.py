from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ShieldProfileBase(BaseModel):
    name: str
    min_reserve_months: float = 2.0
    max_active_expansions: int = 3
    income_drop_percent: float = 0.30
    pause_new_clones: bool = True
    pause_new_zones: bool = True
    reduce_marketing_spend: bool = True
    stop_fun_fund_increase: bool = True
    notes: Optional[str] = None


class ShieldProfileCreate(ShieldProfileBase):
    pass


class ShieldProfileUpdate(BaseModel):
    min_reserve_months: Optional[float]
    max_active_expansions: Optional[int]
    income_drop_percent: Optional[float]
    pause_new_clones: Optional[bool]
    pause_new_zones: Optional[bool]
    reduce_marketing_spend: Optional[bool]
    stop_fun_fund_increase: Optional[bool]
    notes: Optional[str]


class ShieldProfileOut(ShieldProfileBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
