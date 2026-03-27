"""
Pydantic schemas for Offer management.
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from decimal import Decimal


class OfferCreate(BaseModel):
    """Schema for creating an offer."""
    deal_id: int
    offer_price: Decimal = Field(..., gt=0)
    emd_amount: Optional[Decimal] = None
    closing_window_days: Optional[int] = None
    conditions_summary: Optional[str] = None
    generated_by: Optional[str] = None
    status: str = Field(default="draft")


class OfferUpdate(BaseModel):
    """Schema for updating an offer."""
    offer_price: Optional[Decimal] = None
    emd_amount: Optional[Decimal] = None
    closing_window_days: Optional[int] = None
    conditions_summary: Optional[str] = None
    status: Optional[str] = None


class OfferOut(BaseModel):
    """Schema for offer outputs."""
    id: int
    created_at: datetime
    updated_at: datetime
    deal_id: int
    offer_price: Decimal
    emd_amount: Optional[Decimal] = None
    closing_window_days: Optional[int] = None
    conditions_summary: Optional[str] = None
    generated_by: Optional[str] = None
    status: str

    class Config:
        from_attributes = True
