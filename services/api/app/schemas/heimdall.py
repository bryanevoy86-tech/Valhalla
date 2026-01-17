from __future__ import annotations

from datetime import datetime, date
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class HeimdallPolicyOut(BaseModel):
    domain: str
    min_confidence_prod: float
    min_sandbox_trials: int
    min_sandbox_success_rate: float
    prod_use_enabled: bool
    changed_by: Optional[str] = None
    reason: Optional[str] = None
    updated_at: datetime

    class Config:
        from_attributes = True


class HeimdallPolicyUpsertIn(BaseModel):
    domain: str = Field(..., min_length=1, max_length=80)
    min_confidence_prod: float = Field(0.90, ge=0.0, le=1.0)
    min_sandbox_trials: int = Field(50, ge=0)
    min_sandbox_success_rate: float = Field(0.80, ge=0.0, le=1.0)
    prod_use_enabled: bool = False
    changed_by: str = Field(..., min_length=1, max_length=200)
    reason: Optional[str] = Field(None, max_length=1000)


class HeimdallScorecardOut(BaseModel):
    day: date
    domain: str
    trials: int
    successes: int
    success_rate: float
    avg_confidence: float
    updated_at: datetime

    class Config:
        from_attributes = True


class HeimdallRecommendIn(BaseModel):
    domain: str = Field(..., min_length=1, max_length=80)
    confidence: float = Field(..., ge=0.0, le=1.0)
    recommendation: Dict[str, Any]
    evidence: Optional[Dict[str, Any]] = None
    actor: Optional[str] = Field(None, max_length=200)
    correlation_id: Optional[str] = Field(None, max_length=200)


class HeimdallRecommendOut(BaseModel):
    id: int
    domain: str
    confidence: float
    prod_eligible: bool
    gate_reason: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
