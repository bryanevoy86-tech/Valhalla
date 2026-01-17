from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class BRRRRZoneBase(BaseModel):
    code: str
    name: str
    country: str
    min_properties_before_team: int = 5
    current_property_count: int = 0
    currency: str = "CAD"
    language: str = "en"
    timezone: str = "UTC"
    active: bool = False
    legal_profile_code: Optional[str] = None
    notes: Optional[str] = None


class BRRRRZoneCreate(BRRRRZoneBase):
    pass


class BRRRRZoneUpdate(BaseModel):
    name: Optional[str]
    country: Optional[str]
    min_properties_before_team: Optional[int]
    current_property_count: Optional[int]
    currency: Optional[str]
    language: Optional[str]
    timezone: Optional[str]
    active: Optional[bool]
    legal_profile_code: Optional[str]
    notes: Optional[str]


class BRRRRZoneOut(BRRRRZoneBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
