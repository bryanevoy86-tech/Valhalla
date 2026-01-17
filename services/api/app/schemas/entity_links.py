"""
PACK AW: Crosslink / Relationship Graph Schemas
"""

from datetime import datetime
from typing import List
from pydantic import BaseModel


class EntityLinkCreate(BaseModel):
    from_type: str
    from_id: str
    to_type: str
    to_id: str
    relation: str


class EntityLinkOut(BaseModel):
    id: int
    from_type: str
    from_id: str
    to_type: str
    to_id: str
    relation: str
    created_at: datetime

    class Config:
        from_attributes = True
