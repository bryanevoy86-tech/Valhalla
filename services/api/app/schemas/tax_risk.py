from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class TaxRiskProfileBase(BaseModel):
    name: str
    jurisdiction: str = "CRA"
    risk_level: float = 0.5
    meals_percent_cap: float = 0.10
    vehicle_percent_cap: float = 0.30
    home_office_percent_cap: float = 0.20
    travel_percent_cap: float = 0.15
    auto_flag_red: bool = True
    notes: Optional[str] = None


class TaxRiskProfileCreate(TaxRiskProfileBase):
    pass


class TaxRiskProfileUpdate(BaseModel):
    jurisdiction: Optional[str]
    risk_level: Optional[float]
    meals_percent_cap: Optional[float]
    vehicle_percent_cap: Optional[float]
    home_office_percent_cap: Optional[float]
    travel_percent_cap: Optional[float]
    auto_flag_red: Optional[bool]
    notes: Optional[str]


class TaxRiskProfileOut(TaxRiskProfileBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
