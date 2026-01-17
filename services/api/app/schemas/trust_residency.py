"""
PACK AU: Trust & Residency Profile Schemas
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class TrustResidencyCreate(BaseModel):
    subject_type: str = Field(..., description="user, professional, vendor, tenant, etc.")
    subject_id: str = Field(..., description="ID in your system")
    country: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    trust_score: float = Field(50.0, ge=0.0, le=100.0)
    footprint_score: float = Field(0.0, ge=0.0, le=100.0)
    notes: Optional[str] = None


class TrustResidencyUpdate(BaseModel):
    country: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    trust_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    footprint_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    notes: Optional[str] = None


class TrustResidencyOut(BaseModel):
    id: int
    subject_type: str
    subject_id: str
    country: Optional[str]
    region: Optional[str]
    city: Optional[str]
    trust_score: float
    footprint_score: float
    notes: Optional[str]
    updated_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True
