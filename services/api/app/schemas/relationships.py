"""
PACK TN: Trust & Relationship Mapping Schemas
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class RelationshipProfileCreate(BaseModel):
    name: str
    role: Optional[str] = None
    relationship_type: Optional[str] = None
    user_trust_level: Optional[float] = None
    boundaries: Optional[str] = None
    notes: Optional[str] = None


class RelationshipProfileOut(RelationshipProfileCreate):
    id: int

    class Config:
        from_attributes = True


class TrustEventCreate(BaseModel):
    profile_id: int
    event_description: str
    trust_change: Optional[float] = None
    notes: Optional[str] = None


class TrustEventOut(TrustEventCreate):
    id: int
    date: datetime
    visible: bool

    class Config:
        from_attributes = True


class RelationshipMapSnapshot(BaseModel):
    profiles: List[RelationshipProfileOut]
    trust_events: List[TrustEventOut]
