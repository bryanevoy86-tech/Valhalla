"""
PACK SG: Income Routing & Separation Engine
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class IncomeRouteRuleSchema(BaseModel):
    rule_id: str = Field(..., description="Unique rule identifier")
    source: str = Field(..., description="Income source (job, business, rental, etc.)")
    description: Optional[str] = Field(None, description="Human-readable description")
    allocation_type: str = Field(..., description="'percent' or 'fixed'")
    allocation_value: float = Field(..., description="Percentage (0-100) or fixed amount")
    target_account: str = Field(..., description="Target account from banking planner")
    notes: Optional[str] = None
    active: bool = Field(True, description="Is rule active?")

    class Config:
        from_attributes = True


class IncomeEventSchema(BaseModel):
    event_id: str = Field(..., description="Unique event identifier")
    date: datetime = Field(..., description="When income arrived")
    source: str = Field(..., description="Income source")
    amount: int = Field(..., description="Amount in cents")
    notes: Optional[str] = None
    routed: bool = Field(False, description="Has this income been routed?")

    class Config:
        from_attributes = True


class IncomeRoutingLogSchema(BaseModel):
    log_id: str = Field(..., description="Unique log identifier")
    rule_id: int = Field(..., description="Rule that generated this routing")
    income_event_id: str = Field(..., description="Event being routed")
    calculated_amount: int = Field(..., description="Amount in cents")
    target_account: str = Field(..., description="Target account")
    status: str = Field(..., description="pending, approved, executed, or rejected")
    user_approval_date: Optional[datetime] = None
    execution_date: Optional[datetime] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class AllocationDetail(BaseModel):
    target_account: str = Field(..., description="Target account name")
    amount: int = Field(..., description="Amount in cents")
    percent_of_total: float = Field(..., description="Percentage of total income")


class IncomeRoutingSummarySchema(BaseModel):
    summary_id: str = Field(..., description="Unique summary identifier")
    date: datetime = Field(..., description="Date of routing calculation")
    total_income: int = Field(..., description="Total income in cents")
    allocations: List[AllocationDetail] = Field(..., description="Routing allocations")
    unallocated_balance: int = Field(..., description="Amount not allocated in cents")
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class RoutingResponseSchema(BaseModel):
    rule_id: str
    calculated_amount: int
    target_account: str
    status: str
    allocation_percent: float
