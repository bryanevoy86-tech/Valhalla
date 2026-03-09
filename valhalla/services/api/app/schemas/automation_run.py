from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AutomationRunCreate(BaseModel):
    rule_id: int
    rule_name: str
    status: Optional[str] = "started"
    severity: Optional[str] = "info"
    input_snapshot: Optional[str] = None


class AutomationRunUpdate(BaseModel):
    status: Optional[str]
    severity: Optional[str]
    action_result: Optional[str]
    error_message: Optional[str]
    finished_at: Optional[datetime]


class AutomationRunOut(AutomationRunCreate):
    id: int
    action_result: Optional[str]
    error_message: Optional[str]
    created_at: datetime
    finished_at: Optional[datetime]

    class Config:
        orm_mode = True
