from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class BahamasPlanBase(BaseModel):
    name: Optional[str] = "Bahamas Residency & Resort Plan"
    residency_target: float
    residency_vault_balance: float = 0.0
    resort_target_price_min: float = 0.0
    resort_target_price_max: float = 0.0
    resort_vault_balance: float = 0.0
    trigger_residency_ready: bool = False
    trigger_resort_search_active: bool = False
    notes: Optional[str] = None


class BahamasPlanCreate(BahamasPlanBase):
    pass


class BahamasPlanUpdate(BaseModel):
    name: Optional[str]
    residency_target: Optional[float]
    residency_vault_balance: Optional[float]
    resort_target_price_min: Optional[float]
    resort_target_price_max: Optional[float]
    resort_vault_balance: Optional[float]
    trigger_residency_ready: Optional[bool]
    trigger_resort_search_active: Optional[bool]
    notes: Optional[str]


class BahamasPlanOut(BahamasPlanBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
