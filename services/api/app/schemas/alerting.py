from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class AlertChannelBase(BaseModel):
    name: str
    channel_type: str          # "email", "sms", "webhook"
    target: str
    active: bool = True
    notes: Optional[str] = None


class AlertChannelCreate(AlertChannelBase):
    pass


class AlertChannelOut(AlertChannelBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


class AlertRuleBase(BaseModel):
    name: str
    event_type: str
    min_severity: str = "info"
    channel_id: int
    active: bool = True
    notes: Optional[str] = None


class AlertRuleCreate(AlertRuleBase):
    pass


class AlertRuleUpdate(BaseModel):
    min_severity: Optional[str]
    channel_id: Optional[int]
    active: Optional[bool]
    notes: Optional[str]


class AlertRuleOut(AlertRuleBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True
