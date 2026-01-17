from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class MarketPolicyUpsertIn(BaseModel):
    province: str = Field(..., min_length=2, max_length=2)
    market: str = Field("ALL", min_length=1, max_length=40)
    enabled: bool = True
    rules: Dict[str, Any]
    changed_by: str = Field(..., min_length=1, max_length=200)
    reason: Optional[str] = Field(None, max_length=1000)


class MarketPolicyOut(BaseModel):
    province: str
    market: str
    enabled: bool
    rules_json: str
    changed_by: Optional[str] = None
    reason: Optional[str] = None
    updated_at: datetime

    class Config:
        from_attributes = True
