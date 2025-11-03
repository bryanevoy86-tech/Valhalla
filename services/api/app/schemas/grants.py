"""
Grant schemas for API validation and serialization.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import date


class GrantSourceIn(BaseModel):
    name: str = Field(..., max_length=160)
    url: Optional[str] = None
    region: Optional[str] = None
    tags: Optional[str] = None
    active: bool = True


class GrantSourceOut(GrantSourceIn):
    model_config = ConfigDict(from_attributes=True)
    
    id: int


class GrantIn(BaseModel):
    source_id: Optional[int] = None
    title: str = Field(..., max_length=240)
    program: Optional[str] = Field(None, max_length=160)
    category: Optional[str] = Field(None, max_length=120)
    region: Optional[str] = None
    amount_min: Optional[float] = None
    amount_max: Optional[float] = None
    deadline: Optional[date] = None
    link: Optional[str] = None
    summary: Optional[str] = None


class GrantOut(GrantIn):
    model_config = ConfigDict(from_attributes=True)
    
    id: int


class GrantCriteria(BaseModel):
    region: Optional[str] = None          # e.g., "CA-MB"
    categories: Optional[List[str]] = None
    min_amount: Optional[float] = None
    max_deadline: Optional[date] = None
    limit: int = 25


class GrantHit(BaseModel):
    id: int
    title: str
    program: Optional[str] = None
    region: Optional[str] = None
    category: Optional[str] = None
    amount_estimate: Optional[float] = None
    deadline: Optional[date] = None
    link: Optional[str] = None
    score: float
    reason: str


class GrantPack(BaseModel):
    total: int
    hits: List[GrantHit]
