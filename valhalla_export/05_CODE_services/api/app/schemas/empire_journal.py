"""
PACK AS: Empire Journal Engine Schemas
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class JournalEntryCreate(BaseModel):
    entity_type: Optional[str] = Field(
        None, description="deal, property, child, system, self, etc."
    )
    entity_id: Optional[str] = None
    category: str = Field("note", description="note, insight, lesson, risk, win, idea")
    author: Optional[str] = None
    title: Optional[str] = None
    body: str


class JournalEntryOut(BaseModel):
    id: int
    entity_type: Optional[str]
    entity_id: Optional[str]
    category: str
    author: Optional[str]
    title: Optional[str]
    body: str
    created_at: datetime

    class Config:
        from_attributes = True
