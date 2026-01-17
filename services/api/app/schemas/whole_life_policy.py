from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class WholeLifePolicyBase(BaseModel):
    insured_name: str
    owner_entity: str
    policy_number: str
    insurer: Optional[str] = None
    face_value: float = 0.0
    annual_premium: float = 0.0
    cash_value: float = 0.0
    loan_available: float = 0.0
    status: str = "active"
    notes: Optional[str] = None


class WholeLifePolicyCreate(WholeLifePolicyBase):
    pass


class WholeLifePolicyUpdate(BaseModel):
    insured_name: Optional[str]
    owner_entity: Optional[str]
    insurer: Optional[str]
    face_value: Optional[float]
    annual_premium: Optional[float]
    cash_value: Optional[float]
    loan_available: Optional[float]
    status: Optional[str]
    notes: Optional[str]


class WholeLifePolicyOut(WholeLifePolicyBase):
    id: int
    created_at: datetime
    last_updated: datetime

    class Config:
        orm_mode = True
