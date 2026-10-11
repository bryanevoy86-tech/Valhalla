"""
Pydantic schemas for Lead management.

Aligned with canonical database schema for leads table.
"""
from pydantic import BaseModel, EmailStr, Field, model_validator
from datetime import datetime
from typing import Optional
from decimal import Decimal


class LeadCreate(BaseModel):
    """Schema for creating a new lead."""
    lead_name: str = Field(..., min_length=1, max_length=255, description="Seller/contact name")
    lead_email: EmailStr = Field(..., description="Seller/contact email")
    lead_phone: str = Field(..., min_length=1, max_length=20, description="Seller/contact phone")
    
    # Property location (optional at intake)
    property_address: Optional[str] = Field(None, max_length=512)
    property_city: Optional[str] = Field(None, max_length=255)
    property_state: Optional[str] = Field(None, max_length=2)
    property_zip: Optional[str] = Field(None, max_length=10)
    
    # Valuation (optional at intake)
    estimated_arv: Optional[Decimal] = Field(None, ge=0)
    
    # Status and source
    source: str = Field(..., min_length=1, max_length=255, description="Lead source: Zillow, MLS, API, direct, etc")
    lead_status: Optional[str] = Field("new", max_length=50)
    
    # Notes
    notes: Optional[str] = Field(None, description="Additional notes about the lead")

    @model_validator(mode="before")
    @classmethod
    def _compat_legacy_fields(cls, data):
        if not isinstance(data, dict):
            return data

        payload = dict(data)
        if payload.get("lead_name") is None and payload.get("name") is not None:
            payload["lead_name"] = payload.get("name")
        if payload.get("lead_email") is None and payload.get("email") is not None:
            payload["lead_email"] = payload.get("email")
        if payload.get("lead_phone") is None and payload.get("phone") is not None:
            payload["lead_phone"] = payload.get("phone")
        if payload.get("lead_status") is None and payload.get("status") is not None:
            payload["lead_status"] = payload.get("status")

        return payload


class LeadOut(BaseModel):
    """Schema for lead outputs (responses)."""
    id: int
    lead_name: str
    lead_email: str
    lead_phone: str
    property_address: Optional[str] = None
    property_city: Optional[str] = None
    property_state: Optional[str] = None
    property_zip: Optional[str] = None
    estimated_arv: Optional[Decimal] = None
    lead_status: str
    source: str
    notes: Optional[str] = None
    created_ts: datetime
    updated_ts: datetime

    class Config:
        from_attributes = True


class LeadStatusUpdate(BaseModel):
    """Schema for updating lead status."""
    lead_status: str = Field(..., min_length=1, max_length=50)
