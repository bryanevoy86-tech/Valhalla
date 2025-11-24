from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AIPersonaBase(BaseModel):
    name: str
    code: str
    role: str
    domain: str
    status: Optional[str] = "active"
    description: Optional[str] = None
    notes: Optional[str] = None


class AIPersonaCreate(AIPersonaBase):
    pass


class AIPersonaUpdate(BaseModel):
    name: Optional[str]
    code: Optional[str]
    role: Optional[str]
    domain: Optional[str]
    status: Optional[str]
    description: Optional[str]
    notes: Optional[str]


class AIPersonaOut(AIPersonaBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
