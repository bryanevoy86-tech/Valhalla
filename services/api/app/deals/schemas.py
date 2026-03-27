"""
Pydantic schemas for Deal management.

Schemas for validation and serialization of deal data.
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from decimal import Decimal


class DealCreate(BaseModel):
    """Schema for creating a new deal."""
    lead_id: int
    title: str = Field(..., min_length=1, max_length=255)
    stage: str = Field(default="lead_received")
    status: str = Field(default="active")
    arv: Optional[Decimal] = None
    estimated_repair_cost: Optional[Decimal] = None
    max_allowable_offer: Optional[Decimal] = None
    target_assignment_fee: Optional[Decimal] = None
    score: Optional[Decimal] = Field(default=0, ge=0, le=100)
    notes: Optional[str] = None
    disposition_status: Optional[str] = None


class DealUpdate(BaseModel):
    """Schema for updating deal fields."""
    title: Optional[str] = None
    arv: Optional[Decimal] = None
    estimated_repair_cost: Optional[Decimal] = None
    max_allowable_offer: Optional[Decimal] = None
    target_assignment_fee: Optional[Decimal] = None
    score: Optional[Decimal] = None
    notes: Optional[str] = None
    disposition_status: Optional[str] = None


class DealScoreUpdate(BaseModel):
    """Schema for updating deal score."""
    score: Decimal = Field(..., ge=0, le=100)
    notes: Optional[str] = None


class DealStageUpdate(BaseModel):
    """Schema for updating deal stage."""
    new_stage: str = Field(..., min_length=1, max_length=50)
    override_reason: Optional[str] = None


class DealOut(BaseModel):
    """Schema for deal outputs (responses)."""
    id: int
    created_at: datetime
    updated_at: datetime
    lead_id: int
    title: str
    stage: str
    status: str
    arv: Optional[Decimal] = None
    estimated_repair_cost: Optional[Decimal] = None
    max_allowable_offer: Optional[Decimal] = None
    target_assignment_fee: Optional[Decimal] = None
    score: Optional[Decimal] = None
    notes: Optional[str] = None
    disposition_status: Optional[str] = None

    class Config:
        from_attributes = True
