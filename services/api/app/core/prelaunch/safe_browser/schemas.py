"""Safe Browser Schemas"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class KidSearchRequest(BaseModel):
    child_id: UUID
    query: str


class KidSearchResult(BaseModel):
    title: str
    url: str
    snippet: str
    result_type: str = "article"


class KidSearchResponse(BaseModel):
    results: List[KidSearchResult]


class KidNavigateRequest(BaseModel):
    child_id: UUID
    url: str


class PageContent(BaseModel):
    title: str
    text_blocks: list[str]
    media: list[dict] = []


class KidHistoryItem(BaseModel):
    id: UUID
    child_id: UUID
    query: Optional[str] = None
    url: Optional[str] = None
    title: Optional[str] = None
    result_type: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
