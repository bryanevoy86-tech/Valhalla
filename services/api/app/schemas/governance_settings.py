from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class GovernanceSettingsBase(BaseModel):
    name: str
    mode: str = "hybrid"
    max_auto_transfer: float = 1000.0
    max_auto_contract_commit: float = 5000.0
    require_approval_new_zone: bool = True
    require_approval_new_legacy: bool = True
    require_approval_large_hire: bool = True
    shield_always_on: bool = True
    log_all_decisions: bool = True
    notes: Optional[str] = None


class GovernanceSettingsCreate(GovernanceSettingsBase):
    pass


class GovernanceSettingsUpdate(BaseModel):
    mode: Optional[str]
    max_auto_transfer: Optional[float]
    max_auto_contract_commit: Optional[float]
    require_approval_new_zone: Optional[bool]
    require_approval_new_legacy: Optional[bool]
    require_approval_large_hire: Optional[bool]
    shield_always_on: Optional[bool]
    log_all_decisions: Optional[bool]
    notes: Optional[str]


class GovernanceSettingsOut(GovernanceSettingsBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
