from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime


class KnowledgeSourceBase(BaseModel):
    name: str
    category: str
    url: Optional[HttpUrl] = None
    source_type: str = "web"
    engines: str
    active: bool = True
    priority: int = 5
    notes: Optional[str] = None


class KnowledgeSourceCreate(KnowledgeSourceBase):
    pass


class KnowledgeSourceUpdate(BaseModel):
    name: Optional[str]
    category: Optional[str]
    url: Optional[HttpUrl]
    source_type: Optional[str]
    engines: Optional[str]
    active: Optional[bool]
    priority: Optional[int]
    notes: Optional[str]


class KnowledgeSourceOut(KnowledgeSourceBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
