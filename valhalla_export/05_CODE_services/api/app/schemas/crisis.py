"""
PACK TH: Crisis Management Schemas
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class CrisisActionStepBase(BaseModel):
    order: Optional[int] = None
    action: str
    responsible_role: Optional[str] = None
    notes: Optional[str] = None


class CrisisActionStepCreate(CrisisActionStepBase):
    crisis_id: int


class CrisisActionStepOut(CrisisActionStepBase):
    id: int

    class Config:
        from_attributes = True


class CrisisProfileBase(BaseModel):
    name: str
    category: Optional[str] = None
    description: Optional[str] = None
    notes: Optional[str] = None


class CrisisProfileCreate(CrisisProfileBase):
    pass


class CrisisProfileOut(CrisisProfileBase):
    id: int
    steps: List[CrisisActionStepOut] = []

    class Config:
        from_attributes = True


class CrisisLogCreate(BaseModel):
    crisis_id: int
    event: str
    actions_taken: Optional[str] = None
    notes: Optional[str] = None


class CrisisLogOut(BaseModel):
    id: int
    crisis_id: int
    date: datetime
    event: str
    actions_taken: Optional[str] = None
    active: bool
    notes: Optional[str] = None

    class Config:
        from_attributes = True
