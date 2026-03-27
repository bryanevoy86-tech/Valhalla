from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


Frequency = Literal["weekly", "biweekly", "monthly", "quarterly", "annually"]
Status = Literal["active", "paused", "archived"]
Priority = Literal["A", "B", "C", "D"]  # Cone-style priority for obligations


class Recurrence(BaseModel):
    frequency: Frequency = "monthly"
    day_of_month: int = 1               # used for monthly/quarterly/annually
    day_of_week: int = 0                # 0=Mon..6=Sun (weekly/biweekly)
    interval: int = 1                   # future-proof (e.g., every 2 months)
    start_date: str = ""                # YYYY-MM-DD
    timezone: str = "America/Toronto"


class AutopayConfig(BaseModel):
    enabled: bool = False
    verified: bool = False
    method: Literal["bank_autopay", "creditcard_autopay", "e_transfer", "manual"] = "manual"
    payee: str = ""                     # name as in bank
    reference: str = ""                 # account # / customer id
    notes: str = ""


class ObligationCreate(BaseModel):
    name: str                           # "Rent", "Internet", "Water"
    amount: float
    currency: str = "CAD"
    due_day: int = 1                    # convenience default for monthly
    frequency: Frequency = "monthly"
    next_due_date: str = ""             # optional override YYYY-MM-DD
    category: str = "household"
    priority: Priority = "A"
    status: Status = "active"
    pay_from: str = "personal"          # "personal" | "business" (future)
    autopay: AutopayConfig = Field(default_factory=AutopayConfig)
    recurrence: Optional[Recurrence] = None
    tags: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)


class ObligationRecord(BaseModel):
    id: str
    name: str
    amount: float
    currency: str
    due_day: int
    frequency: Frequency
    next_due_date: str = ""
    category: str = "household"
    priority: Priority = "A"
    status: Status
    pay_from: str = "personal"
    autopay: AutopayConfig = Field(default_factory=AutopayConfig)
    recurrence: Recurrence
    tags: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class ObligationListResponse(BaseModel):
    items: List[ObligationRecord]


class AutopayVerifyRequest(BaseModel):
    verified: bool = True
    method: Optional[str] = None
    payee: Optional[str] = None
    reference: Optional[str] = None
    notes: Optional[str] = None
