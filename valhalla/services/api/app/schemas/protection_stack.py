"""PACK 76: Protection Stack - Schemas"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict


class TrustEntityBase(BaseModel):
    name: str
    jurisdiction: str | None = None
    role: str | None = None
    notes: str | None = None


class TrustEntityCreate(TrustEntityBase):
    pass


class TrustEntityOut(TrustEntityBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ShieldModeBase(BaseModel):
    level: str
    active: bool = True
    trigger_reason: str | None = None


class ShieldModeCreate(ShieldModeBase):
    pass


class ShieldModeOut(ShieldModeBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
