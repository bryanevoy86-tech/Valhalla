from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


TargetType = Literal["payment", "receipt", "unknown"]


class ReconSuggestRequest(BaseModel):
    bank_txn_id: str
    max_suggestions: int = 10
    amount_tolerance: float = 1.00      # +/- dollars
    days_tolerance: int = 5             # +/- days
    meta: Dict[str, Any] = Field(default_factory=dict)


class ReconSuggestion(BaseModel):
    target_type: TargetType
    target_id: str
    date: str
    amount: float
    score: float
    reason: str = ""
    snapshot: Dict[str, Any] = Field(default_factory=dict)


class ReconSuggestResponse(BaseModel):
    bank_txn_id: str
    suggestions: List[ReconSuggestion] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class ReconLinkCreate(BaseModel):
    bank_txn_id: str
    target_type: TargetType
    target_id: str
    note: str = ""
    meta: Dict[str, Any] = Field(default_factory=dict)


class ReconLinkRecord(BaseModel):
    id: str
    bank_txn_id: str
    target_type: TargetType
    target_id: str
    note: str = ""
    meta: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
