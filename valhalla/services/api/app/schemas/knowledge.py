from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class KnowledgeSourceBase(BaseModel):
    name: str
    source_type: str
    url: Optional[str] = None
    category: Optional[str] = None
    priority: int = 10
    active: bool = True
    notes: Optional[str] = None


class KnowledgeSourceCreate(KnowledgeSourceBase):
    pass


class KnowledgeSourceUpdate(BaseModel):
    name: Optional[str]
    source_type: Optional[str]
    url: Optional[str]
    category: Optional[str]
    priority: Optional[int]
    active: Optional[bool]
    notes: Optional[str]


class KnowledgeSourceOut(KnowledgeSourceBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
