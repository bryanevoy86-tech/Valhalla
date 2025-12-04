from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AIPersonaBase(BaseModel):
    name: str
    code: str
    role: str
    description: Optional[str] = None
    primary_domains: Optional[str] = None   # comma-separated
    active: bool = True
    tone: str = "neutral"
    safety_level: str = "high"
    notes: Optional[str] = None


class AIPersonaCreate(AIPersonaBase):
    pass


class AIPersonaUpdate(BaseModel):
    role: Optional[str]
    description: Optional[str]
    primary_domains: Optional[str]
    active: Optional[bool]
    tone: Optional[str]
    safety_level: Optional[str]
    notes: Optional[str]


class AIPersonaOut(AIPersonaBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
