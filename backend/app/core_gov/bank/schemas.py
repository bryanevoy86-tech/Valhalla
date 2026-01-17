from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


TxnType = Literal["debit", "credit", "unknown"]
Status = Literal["new", "reconciled", "ignored", "archived"]


class BankTxnCreate(BaseModel):
    date: str                      # "YYYY-MM-DD"
    description: str
    amount: float
    currency: str = "CAD"
    txn_type: TxnType = "unknown"
    account: str = ""              # "RBC chequing", etc.
    status: Status = "new"
    external_id: str = ""          # bank id if available
    tags: List[str] = Field(default_factory=list)
    notes: str = ""
    meta: Dict[str, Any] = Field(default_factory=dict)


class BankTxnRecord(BaseModel):
    id: str
    date: str
    description: str
    amount: float
    currency: str
    txn_type: TxnType
    account: str
    status: Status
    external_id: str = ""
    tags: List[str] = Field(default_factory=list)
    notes: str = ""
    meta: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class BankTxnListResponse(BaseModel):
    items: List[BankTxnRecord]
