from __future__ import annotations

from datetime import datetime, date
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class RiskPolicyOut(BaseModel):
    engine: str
    max_daily_loss: float
    max_daily_exposure: float
    max_open_risk: float
    max_actions_per_day: int
    enabled: bool
    changed_by: Optional[str] = None
    reason: Optional[str] = None
    updated_at: datetime

    class Config:
        from_attributes = True


class RiskPolicyUpsertIn(BaseModel):
    engine: str = Field(..., min_length=1, max_length=50)

    max_daily_loss: float = Field(..., ge=0)
    max_daily_exposure: float = Field(..., ge=0)
    max_open_risk: float = Field(..., ge=0)

    max_actions_per_day: int = Field(0, ge=0)
    enabled: bool = True

    changed_by: str = Field(..., min_length=1, max_length=200)
    reason: Optional[str] = Field(None, max_length=1000)


class RiskLedgerOut(BaseModel):
    day: date
    engine: str
    exposure_used: float
    open_risk_reserved: float
    realized_loss: float
    actions_count: int
    updated_at: datetime

    class Config:
        from_attributes = True


class RiskCheckIn(BaseModel):
    engine: str = Field(..., min_length=1, max_length=50)
    amount: float = Field(..., gt=0)  # exposure to reserve for this action
    actor: Optional[str] = Field(None, max_length=200)
    reason: Optional[str] = Field(None, max_length=1000)
    correlation_id: Optional[str] = Field(None, max_length=200)
    metadata: Optional[Dict[str, Any]] = None


class RiskCheckOut(BaseModel):
    ok: bool
    engine: str
    reserved: float = 0.0
    message: str
    policy_snapshot: Dict[str, Any]
    ledger_snapshot: Dict[str, Any]
