from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class BahamasVaultBase(BaseModel):
    name: str = "Bahamas Residency Vault"
    current_balance: float = 0.0
    target_balance: float = 0.0
    min_resort_price: float = 0.0
    max_resort_price: float = 0.0
    percent_to_target: float = 0.0
    residency_ready: bool = False
    resort_search_active: bool = False
    notes: Optional[str] = None


class BahamasVaultCreate(BahamasVaultBase):
    pass


class BahamasVaultUpdate(BaseModel):
    name: Optional[str]
    current_balance: Optional[float]
    target_balance: Optional[float]
    min_resort_price: Optional[float]
    max_resort_price: Optional[float]
    percent_to_target: Optional[float]
    residency_ready: Optional[bool]
    resort_search_active: Optional[bool]
    notes: Optional[str]


class BahamasVaultOut(BahamasVaultBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
