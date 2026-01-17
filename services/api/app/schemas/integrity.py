from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class IntegrityEventCreate(BaseModel):
    source: str
    category: str
    action: str
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    severity: str = "info"
    message: str
    payload: Optional[str] = None


class IntegrityEventOut(IntegrityEventCreate):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True
