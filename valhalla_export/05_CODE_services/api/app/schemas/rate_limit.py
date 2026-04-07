"""
PACK UC: Rate Limiting & Quota Engine Schemas
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class RateLimitRuleSet(BaseModel):
    scope: str
    key: str
    window_seconds: int = 60
    max_requests: int = 60
    enabled: bool = True
    description: Optional[str] = None


class RateLimitRuleOut(RateLimitRuleSet):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RateLimitRuleList(BaseModel):
    total: int
    items: List[RateLimitRuleOut]


class RateLimitSnapshotOut(BaseModel):
    id: int
    scope: str
    key: str
    window_seconds: int
    max_requests: int
    current_count: int
    window_started_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
