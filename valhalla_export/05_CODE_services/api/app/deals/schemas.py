"""
Pydantic schemas for Deal management.

Schemas for validation and serialization of deal data.
"""
from pydantic import BaseModel, Field, ConfigDict, field_serializer
from datetime import datetime
from typing import Optional
from decimal import Decimal


class DealCreate(BaseModel):
    """Schema for creating a new deal from a lead."""
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


class DealCreateDirect(BaseModel):
    """Schema for creating a standalone deal (auto-creates placeholder lead if needed)."""
    lead_id: Optional[int] = None  # Optional - auto-creates placeholder lead if not provided
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
    """Schema for deal outputs (responses) - with JSON-safe serialization."""
    id: int
    created_ts: datetime
    updated_ts: datetime
    lead_id: int
    title: str
    stage: str
    status: str
    # Accept Decimal from ORM, serialize as str
    arv: Optional[Decimal] = None
    estimated_repair_cost: Optional[Decimal] = None
    max_allowable_offer: Optional[Decimal] = None
    target_assignment_fee: Optional[Decimal] = None
    score: Optional[Decimal] = None
    notes: Optional[str] = None
    disposition_status: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    @field_serializer('arv', 'estimated_repair_cost', 'max_allowable_offer', 'target_assignment_fee', 'score', when_used='json')
    def serialize_decimals(self, value: Optional[Decimal]) -> Optional[str]:
        """Convert Decimal fields to strings for JSON serialization."""
        if value is None:
            return None
        return str(value)
