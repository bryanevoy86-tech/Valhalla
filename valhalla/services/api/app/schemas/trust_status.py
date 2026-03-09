from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class TrustStatusBase(BaseModel):
    trust_code: str
    display_name: str
    lawyer_engaged: bool = False
    draft_complete: bool = False
    signed: bool = False
    bank_accounts_open: bool = False
    life_policies_assigned: bool = False
    property_titled: bool = False
    status: Optional[str] = "pending"
    notes: Optional[str] = None


class TrustStatusCreate(TrustStatusBase):
    pass


class TrustStatusUpdate(BaseModel):
    lawyer_engaged: Optional[bool]
    draft_complete: Optional[bool]
    signed: Optional[bool]
    bank_accounts_open: Optional[bool]
    life_policies_assigned: Optional[bool]
    property_titled: Optional[bool]
    status: Optional[str]
    notes: Optional[str]


class TrustStatusOut(TrustStatusBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
