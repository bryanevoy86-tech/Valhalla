"""Pack 58: Resort - Schemas"""
from pydantic import BaseModel
from typing import Optional, List

class ProjectIn(BaseModel):
    name: str
    currency: str = "USD"
    target_budget: float

class VaultInflow(BaseModel):
    project_id: int
    amount: float
    note: Optional[str] = None

class VaultOutflow(BaseModel):
    project_id: int
    amount: float
    note: Optional[str] = None

class MilestoneIn(BaseModel):
    project_id: int
    code: str
    name: str
    due_date: Optional[str] = None

class StepIn(BaseModel):
    timeline_id: int
    code: str
    name: str
    due_date: Optional[str] = None

class QuoteIn(BaseModel):
    project_id: int
    vendor: str
    scope: str
    amount: float
    currency: str = "USD"

class FundingIn(BaseModel):
    project_id: int
    source: str
    program_name: Optional[str] = None
    amount: float
    currency: str = "USD"

class ResidencyIn(BaseModel):
    country: str = "Bahamas"
    target_date: Optional[str] = None
    min_capital: float = 0.0
    note: Optional[str] = None

class DigestOut(BaseModel):
    lines: List[str]
