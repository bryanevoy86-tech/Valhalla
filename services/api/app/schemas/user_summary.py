"""
PACK AT: User-Facing Summary Snapshot Schemas
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class UserSummaryCreate(BaseModel):
    summary_type: str = Field("custom", description="daily, weekly, monthly, milestone, custom")
    audience: Optional[str] = Field(None, description="family, kids, founders, ops, etc.")
    title: Optional[str] = None
    body: str
    created_by: Optional[str] = None


class UserSummaryOut(BaseModel):
    id: int
    summary_type: str
    audience: Optional[str]
    title: Optional[str]
    body: str
    created_by: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
