"""
PACK TE: Life Roles & Capacity Engine Schemas
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class LifeRoleCreate(BaseModel):
    name: str = Field(..., description="Role name (e.g., Father, Builder, Operator)")
    domain: Optional[str] = Field(None, description="Domain or category")
    description: Optional[str] = Field(None, description="What this role means to you")
    priority: Optional[int] = Field(None, ge=1, le=5, description="1–5 priority scale")


class LifeRoleOut(LifeRoleCreate):
    id: int

    class Config:
        from_attributes = True


class RoleCapacityCreate(BaseModel):
    role_id: int = Field(..., description="Which role's capacity to record")
    date: datetime = Field(default_factory=datetime.utcnow, description="Snapshot date")
    load_level: float = Field(..., ge=0.0, le=1.0, description="0.0 (free) to 1.0 (maxed)")
    notes: Optional[str] = Field(None, description="Context about load level")


class RoleCapacityOut(RoleCapacityCreate):
    id: int

    class Config:
        from_attributes = True
