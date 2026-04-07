"""
PACK CI8: Narrative / Chapter Engine Schemas
"""

from datetime import datetime
from typing import Optional, Any, Dict, List
from pydantic import BaseModel


class NarrativeChapterIn(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    phase_order: int = 1
    goals: Optional[Dict[str, Any]] = None
    exit_conditions: Optional[Dict[str, Any]] = None


class NarrativeChapterOut(NarrativeChapterIn):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class NarrativeChapterList(BaseModel):
    total: int
    items: List[NarrativeChapterOut]


class NarrativeEventIn(BaseModel):
    chapter_id: int
    title: str
    description: Optional[str] = None
    tags: Optional[Dict[str, Any]] = None
    occurred_at: Optional[datetime] = None


class NarrativeEventOut(BaseModel):
    id: int
    chapter_id: int
    title: str
    description: Optional[str]
    tags: Optional[Dict[str, Any]]
    occurred_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class NarrativeEventList(BaseModel):
    total: int
    items: List[NarrativeEventOut]


class ActiveChapterSet(BaseModel):
    chapter_id: int
    reason: Optional[str] = None


class ActiveChapterOut(BaseModel):
    id: int
    chapter_id: int
    changed_at: datetime
    reason: Optional[str]

    class Config:
        from_attributes = True
