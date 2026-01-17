from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class IntegrityEventBase(BaseModel):
    event_type: str
    severity: str = "info"
    actor_type: str
    actor_name: str
    legacy_code: Optional[str] = None
    vault_name: Optional[str] = None
    amount: float = 0.0
    currency: str = "CAD"
    description: Optional[str] = None
    metadata_json: Optional[str] = None
    requires_human_review: bool = False
    reviewed: bool = False
    review_note: Optional[str] = None


class IntegrityEventCreate(IntegrityEventBase):
    pass


class IntegrityEventUpdate(BaseModel):
    reviewed: Optional[bool]
    review_note: Optional[str]


class IntegrityEventOut(IntegrityEventBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True
