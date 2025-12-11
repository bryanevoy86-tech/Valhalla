"""PACK 73: Alerts & SLA Schemas
Pydantic models for alert rules and events.
"""

from pydantic import BaseModel
from typing import Optional


class AlertRuleBase(BaseModel):
    name: str
    description: Optional[str] = None
    condition_payload: str


class AlertRuleCreate(AlertRuleBase):
    pass


class AlertRuleOut(AlertRuleBase):
    id: int
    active: bool

    class Config:
        from_attributes = True


class AlertEventBase(BaseModel):
    rule_id: Optional[int] = None
    level: str
    message: str


class AlertEventCreate(AlertEventBase):
    pass


class AlertEventOut(AlertEventBase):
    id: int

    class Config:
        from_attributes = True
