from pydantic import BaseModel
from typing import Optional

class LegalProfileBase(BaseModel):
    country: str
    region: Optional[str] = None
    profile_name: str
    category: Optional[str] = None
    risk_level: Optional[str] = "medium"
    notes: Optional[str] = None

class LegalProfileCreate(LegalProfileBase):
    active: bool = True

class LegalProfileUpdate(BaseModel):
    country: Optional[str]
    region: Optional[str]
    profile_name: Optional[str]
    category: Optional[str]
    risk_level: Optional[str]
    notes: Optional[str]
    active: Optional[bool]

class LegalProfileOut(LegalProfileBase):
    id: int
    active: bool

    class Config:
        orm_mode = True
