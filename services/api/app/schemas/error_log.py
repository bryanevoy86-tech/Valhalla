from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ErrorLogCreate(BaseModel):
    source: str
    location: Optional[str] = None
    severity: Optional[str] = "error"
    message: str
    stacktrace: Optional[str] = None
    context: Optional[str] = None


class ErrorLogUpdate(BaseModel):
    resolved: Optional[bool]
    resolved_note: Optional[str]
    resolved_at: Optional[datetime]


class ErrorLogOut(ErrorLogCreate):
    id: int
    resolved: bool
    resolved_note: Optional[str]
    created_at: datetime
    resolved_at: Optional[datetime]

    class Config:
        orm_mode = True
