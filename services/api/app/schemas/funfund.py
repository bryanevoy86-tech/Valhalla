from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class FunFundRoutingBase(BaseModel):
    profile_name: str
    arbitrage_percent: float = 1.0
    min_liquid_balance: float = 0.0
    max_liquid_balance: float = 1_000_000.0
    risk_profile: Optional[str] = "moderate"
    active: bool = True
    description: Optional[str] = None


class FunFundRoutingCreate(FunFundRoutingBase):
    pass


class FunFundRoutingUpdate(BaseModel):
    arbitrage_percent: Optional[float]
    min_liquid_balance: Optional[float]
    max_liquid_balance: Optional[float]
    risk_profile: Optional[str]
    active: Optional[bool]
    description: Optional[str]


class FunFundRoutingOut(FunFundRoutingBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
