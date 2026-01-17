from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class KnowledgeCreate(BaseModel):
    source: str
    title: Optional[str] = None
    content: str
    tags: Optional[str] = None
    ttl_hours: Optional[int] = 168  # default 7 days


class KnowledgeResponse(BaseModel):
    id: int
    source: str
    title: Optional[str]
    content: str
    tags: Optional[str]
    expires_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True
