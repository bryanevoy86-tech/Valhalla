from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class ExternalExpertBase(BaseModel):
    name: str
    firm: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    specialty: str
    jurisdiction: Optional[str] = None
    hourly_rate: float = 0.0
    preferred: bool = True
    notes: Optional[str] = None


class ExternalExpertCreate(ExternalExpertBase):
    pass


class ExternalExpertUpdate(BaseModel):
    firm: Optional[str]
    email: Optional[EmailStr]
    phone: Optional[str]
    hourly_rate: Optional[float]
    preferred: Optional[bool]
    jurisdiction: Optional[str]
    notes: Optional[str]
    last_contacted_at: Optional[datetime]


class ExternalExpertOut(ExternalExpertBase):
    id: int
    last_contacted_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
