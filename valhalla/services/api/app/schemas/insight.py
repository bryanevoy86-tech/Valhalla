"""
PACK CI4: Insight Synthesizer Schemas
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class InsightIn(BaseModel):
    source: str = "heimdall"
    category: str
    title: str
    body: str
    importance: int = 5
    tags: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None


class InsightOut(InsightIn):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class InsightList(BaseModel):
    total: int
    items: List[InsightOut]
