from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID
from pydantic import BaseModel


class HumanSpecialistBase(BaseModel):
    name: str
    role: str
    email: Optional[str] = None
    phone: Optional[str] = None
    notes: Optional[str] = None
    expertise: Optional[dict[str, Any]] = None


class HumanSpecialistCreate(HumanSpecialistBase):
    pass


class HumanSpecialistRead(HumanSpecialistBase):
    id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class SpecialistCommentCreate(BaseModel):
    comment: Optional[str] = None
    payload: Optional[dict[str, Any]] = None


class SpecialistCaseCommentRead(BaseModel):
    id: UUID
    created_at: datetime
    specialist_id: UUID
    case_id: UUID
    comment: Optional[str] = None
    payload: Optional[dict[str, Any]] = None

    model_config = {"from_attributes": True}
