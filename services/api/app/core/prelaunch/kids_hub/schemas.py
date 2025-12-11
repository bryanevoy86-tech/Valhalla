"""Kids Hub Schemas"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class ChildProfileCreate(BaseModel):
    name: str
    nickname: Optional[str] = None
    age: Optional[str] = None
    preferences: Optional[dict] = None


class ChildProfileRead(BaseModel):
    id: UUID
    name: str
    nickname: Optional[str] = None
    age: Optional[str] = None
    preferences: Optional[dict] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChildTaskCreate(BaseModel):
    title: str
    description: Optional[str] = None


class ChildTaskRead(BaseModel):
    id: UUID
    child_id: UUID
    title: str
    description: Optional[str] = None
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
