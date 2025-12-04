from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class LegalProfileBase(BaseModel):
    code: str
    country: str
    region: Optional[str] = None
    description: Optional[str] = None
    requires_local_corp: bool = False
    allows_foreign_ownership: bool = True
    brrrr_refi_restricted: bool = False
    short_term_rental_restricted: bool = False
    eviction_strict: bool = False
    license_required: bool = False
    notes: Optional[str] = None


class LegalProfileCreate(LegalProfileBase):
    pass


class LegalProfileUpdate(BaseModel):
    country: Optional[str]
    region: Optional[str]
    description: Optional[str]
    requires_local_corp: Optional[bool]
    allows_foreign_ownership: Optional[bool]
    brrrr_refi_restricted: Optional[bool]
    short_term_rental_restricted: Optional[bool]
    eviction_strict: Optional[bool]
    license_required: Optional[bool]
    notes: Optional[str]


class LegalProfileOut(LegalProfileBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
