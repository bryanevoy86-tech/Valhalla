from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional, Dict, Any

class Source(BaseModel):
    name: str
    url: HttpUrl
    type: str = 'doc'  # doc, api, dataset
    tags: List[str] = []

class SearchQuery(BaseModel):
    q: str = Field(..., description="query text")
    limit: int = 8
    tags: Optional[List[str]] = None

class Result(BaseModel):
    title: str
    url: HttpUrl
    snippet: Optional[str] = None
    meta: Dict[str, Any] = {}

class SearchResponse(BaseModel):
    query: str
    results: List[Result] = []
    cached: bool = False

class Playbook(BaseModel):
    key: str
    title: str
    steps: List[str]
    tags: List[str] = []
    meta: Dict[str, Any] = {}

class UpsertPlaybook(BaseModel):
    title: str
    steps: List[str]
    tags: List[str] = []
    meta: Dict[str, Any] = {}
