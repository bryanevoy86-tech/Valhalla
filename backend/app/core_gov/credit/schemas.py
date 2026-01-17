from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


AccountType = Literal["credit_card", "line_of_credit", "vendor_tradeline", "loan", "other"]
Status = Literal["active", "closed", "paused"]
Bureau = Literal["equifax", "transunion", "experian", "other"]


class CreditProfileUpsert(BaseModel):
    business_name: str = "Valhalla Legacy Inc."
    country: str = "CA"
    province: str = ""
    incorporation_date: str = ""
    ein_bn: str = ""
    address: str = ""
    phone: str = ""
    website: str = ""
    email: str = ""
    meta: Dict[str, Any] = Field(default_factory=dict)


class CreditAccountCreate(BaseModel):
    name: str
    account_type: AccountType = "credit_card"
    status: Status = "active"
    bureau_reporting: List[Bureau] = Field(default_factory=list)
    opened_date: str = ""
    credit_limit: float = 0.0
    balance: float = 0.0
    due_day: int = 1
    autopay: bool = False
    notes: str = ""
    tags: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)


class CreditAccountRecord(BaseModel):
    id: str
    name: str
    account_type: AccountType
    status: Status
    bureau_reporting: List[Bureau] = Field(default_factory=list)
    opened_date: str = ""
    credit_limit: float = 0.0
    balance: float = 0.0
    utilization: float = 0.0
    due_day: int = 1
    autopay: bool = False
    notes: str = ""
    tags: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class CreditListResponse(BaseModel):
    profile: Dict[str, Any]
    accounts: List[CreditAccountRecord]
    totals: Dict[str, Any]


class UtilUpdate(BaseModel):
    account_id: str
    balance: float
    credit_limit: Optional[float] = None


class CreditTask(BaseModel):
    id: str
    title: str
    due_date: str
    priority: Literal["A", "B", "C", "D"] = "B"
    status: Literal["open", "done", "canceled"] = "open"
    meta: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
