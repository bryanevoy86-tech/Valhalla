"""PACK 93: Multi-Zone Expansion - Schemas"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict


class BusinessZoneBase(BaseModel):
    name: str
    region_code: str
    notes: str | None = None


class BusinessZoneCreate(BusinessZoneBase):
    pass


class BusinessZoneOut(BusinessZoneBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
