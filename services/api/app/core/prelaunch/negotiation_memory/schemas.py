"""Negotiation Memory Schemas"""
from datetime import datetime
from typing import Optional, Any, List
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class NegotiationOutcomeCreate(BaseModel):
    category: str
    style_used: str
    outcome: str
    confidence: Optional[float] = None
    notes: Optional[str] = None
    outcome_metadata: Optional[dict[str, Any]] = None


class NegotiationOutcomeRead(BaseModel):
    id: UUID
    category: str
    style_used: str
    outcome: str
    confidence: Optional[float] = None
    notes: Optional[str] = None
    outcome_metadata: Optional[dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NegotiationStats(BaseModel):
    category: str
    style_used: str
    total: int
    wins: int
    losses: int
    win_rate: float
