"""
Pack 53: Black Ice Tier II + Shadow Contingency - Pydantic schemas
"""
from pydantic import BaseModel
from typing import Optional, List

class ProtocolIn(BaseModel):
    name: str
    level: int = 2
    description: Optional[str] = None

class ProtocolOut(ProtocolIn):
    id: int
    active: bool
    created_at: Optional[str] = None
    class Config: from_attributes = True

class EventIn(BaseModel):
    protocol_id: int
    event_type: str
    details: Optional[str] = None

class EventOut(EventIn):
    id: int
    occurred_at: Optional[str] = None
    class Config: from_attributes = True

class KeyCheckIn(BaseModel):
    protocol_id: int
    checklist_item: str

class KeyCheckOut(KeyCheckIn):
    id: int
    checked: bool
    checked_at: Optional[str] = None
    class Config: from_attributes = True

class ContinuityIn(BaseModel):
    protocol_id: int
    min_hours: int = 72
    alert_channel: str = "ops"
    notes: Optional[str] = None

class ContinuityOut(ContinuityIn):
    id: int
    active: bool
    class Config: from_attributes = True
