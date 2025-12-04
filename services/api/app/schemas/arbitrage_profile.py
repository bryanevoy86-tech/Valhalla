from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ArbitrageProfileBase(BaseModel):
    name: str
    pool_type: str                  # "fun_fund" or "treasury"
    risk_level: float = 0.3
    liquidity_priority: float = 0.9
    max_exposure_fraction: float = 0.5
    min_cash_buffer_fraction: float = 0.2
    auto_trading_enabled: bool = True
    notes: Optional[str] = None


class ArbitrageProfileCreate(ArbitrageProfileBase):
    pass


class ArbitrageProfileUpdate(BaseModel):
    risk_level: Optional[float]
    liquidity_priority: Optional[float]
    max_exposure_fraction: Optional[float]
    min_cash_buffer_fraction: Optional[float]
    auto_trading_enabled: Optional[bool]
    notes: Optional[str]


class ArbitrageProfileOut(ArbitrageProfileBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
