"""
Pack 50: Full Accounting Suite - Pydantic schemas
"""
from pydantic import BaseModel
from pydantic import ConfigDict
from typing import Optional, List, Literal, Dict

AccountType = Literal["asset","liability","equity","income","expense"]


class AccountIn(BaseModel):
    code: str
    name: str
    type: AccountType
    currency: str = "CAD"
    active: bool = True


class AccountOut(AccountIn):
    id: int
    model_config = ConfigDict(from_attributes=True)


class JournalLineIn(BaseModel):
    account_code: str
    debit: float = 0
    credit: float = 0
    tax_code: Optional[str] = None
    tag: Optional[str] = None


class JournalEntryIn(BaseModel):
    entry_date: str
    memo: Optional[str] = None
    source: Optional[str] = None
    source_ref: Optional[str] = None
    lines: List[JournalLineIn]


class PostResult(BaseModel):
    entry_id: int
    balanced: bool


class PeriodIn(BaseModel):
    label: str
    start_date: str
    end_date: str


class ReportReq(BaseModel):
    period_label: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class PnLRow(BaseModel):
    name: str
    amount: float


class PnLReport(BaseModel):
    currency: str
    income: List[PnLRow]
    expense: List[PnLRow]
    net_income: float


class TBRow(BaseModel):
    account: str
    debit: float
    credit: float


class TBReport(BaseModel):
    currency: str
    rows: List[TBRow]


class TaxReport(BaseModel):
    totals_by_code: Dict[str, float]
    totals_by_category: Dict[str, float]


class CRASummary(BaseModel):
    period_label: str
    risk_score: float
    summary: str
