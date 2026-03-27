from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


TxType = Literal["income", "expense"]
Status = Literal["posted", "void"]
Priority = Literal["A", "B", "C", "D"]


class TransactionCreate(BaseModel):
    tx_type: TxType
    amount: float
    currency: str = "CAD"
    date: str                      # YYYY-MM-DD
    description: str
    bucket_id: str = ""            # optional, but recommended
    priority: Priority = "B"
    status: Status = "posted"
    merchant: str = ""
    category: str = ""             # free-text helper
    link_type: str = ""            # obligation/flow/replacement/etc
    link_id: str = ""
    notes: str = ""
    tags: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)


class TransactionRecord(BaseModel):
    id: str
    tx_type: TxType
    amount: float
    currency: str
    date: str
    description: str
    bucket_id: str = ""
    priority: Priority
    status: Status
    merchant: str = ""
    category: str = ""
    link_type: str = ""
    link_id: str = ""
    notes: str = ""
    tags: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class TransactionListResponse(BaseModel):
    items: List[TransactionRecord]
