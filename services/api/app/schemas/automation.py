from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AutomationRuleBase(BaseModel):
    name: str
    category: Optional[str] = "general"
    active: bool = True
    trigger_expression: str
    action_expression: str
    description: Optional[str] = None


class AutomationRuleCreate(AutomationRuleBase):
    pass


class AutomationRuleUpdate(BaseModel):
    name: Optional[str]
    category: Optional[str]
    active: Optional[bool]
    trigger_expression: Optional[str]
    action_expression: Optional[str]
    description: Optional[str]


class AutomationRuleOut(AutomationRuleBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
