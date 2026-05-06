"""
Schemas for VA (Virtual Assistant) lead intake and Heimdall scoring.
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal


class VALeadIntakeCreate(BaseModel):
    source_platform: str = Field(..., examples=["facebook", "kijiji", "google_maps", "city_site", "manual", "referral"])
    source_type: str = Field(default="manual_va", examples=["manual_va", "manual_owner", "public_listing", "referral"])
    source_url: Optional[str] = None

    address: Optional[str] = None
    city: Optional[str] = "Winnipeg"
    province: Optional[str] = "MB"

    seller_name: Optional[str] = None
    seller_phone: Optional[str] = None
    seller_email: Optional[str] = None

    asking_price: Optional[float] = None
    raw_text: str
    va_notes: Optional[str] = None

    strategy_fit: Optional[str] = Field(default="wholesale", examples=["wholesale", "brrr", "flip", "rental", "unknown"])
    submitted_by: Optional[str] = "va"


class VALeadIntakeResult(BaseModel):
    success: bool = True
    lead_id: str
    lead_status: str
    source_platform: str
    heimdall_score: int
    risk_level: Literal["low", "medium", "high"]
    confidence: float
    recommended_action: str
    approval_required: bool = True
    next_pipeline_stage: str
    reasoning_summary: str
