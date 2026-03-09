from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class LegacyCloneProfileBase(BaseModel):
    name: str
    min_monthly_income: float = 0.0
    min_reserve_months: float = 2.0
    min_legacy_count: int = 1
    max_legacies: int = 100
    require_all_green_health: bool = True
    auto_clone_enabled: bool = True
    clones_per_batch: int = 1
    max_new_clones_per_year: int = 10
    notes: Optional[str] = None


class LegacyCloneProfileCreate(LegacyCloneProfileBase):
    pass


class LegacyCloneProfileUpdate(BaseModel):
    min_monthly_income: Optional[float]
    min_reserve_months: Optional[float]
    min_legacy_count: Optional[int]
    max_legacies: Optional[int]
    require_all_green_health: Optional[bool]
    auto_clone_enabled: Optional[bool]
    clones_per_batch: Optional[int]
    max_new_clones_per_year: Optional[int]
    notes: Optional[str]


class LegacyCloneProfileOut(LegacyCloneProfileBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
