from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class FreezeRuleCreate(BaseModel):
    name: str
    metric: str
    threshold: float
    comparator: str = ">"
    active: bool = True
    scope: Optional[str] = None


class FreezeRuleResponse(FreezeRuleCreate):
    id: int

    class Config:
        from_attributes = True


class FreezeEventResponse(BaseModel):
    id: int
    rule_name: str
    triggered_value: float
    message: str
    created_at: datetime
    resolved: bool

    class Config:
        from_attributes = True
