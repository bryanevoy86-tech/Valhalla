"""
PACK AE: Public Investor Module Schemas
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class InvestorProfileCreate(BaseModel):
    user_id: int
    full_name: Optional[str] = None
    email: Optional[str] = None
    is_accredited: bool = False
    country: Optional[str] = None
    strategy_preference: Optional[str] = Field(None, description="income, growth, or mixed")
    risk_tolerance: Optional[str] = Field(None, description="conservative, moderate, or higher")
    notes: Optional[str] = None


class InvestorProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    is_accredited: Optional[bool] = None
    country: Optional[str] = None
    strategy_preference: Optional[str] = None
    risk_tolerance: Optional[str] = None
    notes: Optional[str] = None


class InvestorProfileOut(BaseModel):
    id: int
    user_id: int
    full_name: Optional[str]
    email: Optional[str]
    is_accredited: bool
    country: Optional[str]
    strategy_preference: Optional[str]
    risk_tolerance: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InvestorProjectCreate(BaseModel):
    slug: str = Field(..., description="URL-friendly slug, e.g. 'bahamas-resort-1'")
    title: str
    region: Optional[str] = None
    description: Optional[str] = None
    status: str = Field("research", description="research, open, or closed")
    notes: Optional[str] = None


class InvestorProjectUpdate(BaseModel):
    title: Optional[str] = None
    region: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class InvestorProjectOut(BaseModel):
    id: int
    slug: str
    title: str
    region: Optional[str]
    description: Optional[str]
    status: str
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
