"""
PACK SI: Real Estate Acquisition & BRRRR Planner
Pydantic schemas for BRRRR deal tracking
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class BRRRRDealSchema(BaseModel):
    deal_id: str = Field(..., description="Unique deal identifier")
    address: str = Field(..., description="Property address")
    description: Optional[str] = Field(None, description="Deal description")
    purchase_price: int = Field(..., description="Purchase price in cents")
    reno_budget: int = Field(..., description="Renovation budget in cents")
    arv: Optional[int] = Field(None, description="After-repair value in cents (user-provided)")
    strategy_notes: Optional[str] = Field(None, description="Deal strategy notes")
    acquisition_date: Optional[datetime] = None
    reno_start_date: Optional[datetime] = None
    reno_end_date: Optional[datetime] = None
    refinance_date: Optional[datetime] = None
    status: str = Field("analysis", description="analysis, in_progress, refinanced, or holding")

    class Config:
        from_attributes = True


class BRRRRFundingPlanSchema(BaseModel):
    plan_id: str = Field(..., description="Unique plan identifier")
    deal_id: int
    down_payment: int = Field(..., description="Down payment in cents")
    renovation_funds_source: Optional[str] = Field(None, description="Funding source for reno")
    holding_costs_plan: Optional[str] = Field(None, description="How holding costs are covered")
    refinance_strategy: Optional[str] = Field(None, description="Refinance plan")
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class BRRRRCashflowEntrySchema(BaseModel):
    entry_id: str = Field(..., description="Unique entry identifier")
    deal_id: int
    date: datetime = Field(..., description="Period end date")
    rent: int = Field(..., description="Rent income in cents")
    expenses: int = Field(..., description="Expenses in cents")
    net: int = Field(..., description="Net cashflow in cents")
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class BRRRRRefinanceSnapshotSchema(BaseModel):
    snapshot_id: str = Field(..., description="Unique snapshot identifier")
    deal_id: int
    date: datetime = Field(..., description="Refinance date")
    new_loan_amount: int = Field(..., description="New loan amount in cents")
    interest_rate: float = Field(..., description="Interest rate %")
    loan_term_months: Optional[int] = Field(None, description="Loan term in months")
    cash_out_amount: int = Field(..., description="Cash out in cents")
    new_payment: int = Field(..., description="New monthly payment in cents")
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class BRRRRSummarySchema(BaseModel):
    summary_id: str = Field(..., description="Unique summary identifier")
    deal_id: int
    purchase_price: int = Field(..., description="Purchase price in cents")
    reno_actual: Optional[int] = Field(None, description="Actual reno cost in cents")
    reno_budget: Optional[int] = Field(None, description="Budgeted reno in cents")
    arv: Optional[int] = Field(None, description="After-repair value in cents")
    initial_equity: Optional[int] = Field(None, description="Initial equity in cents")
    refi_loan_amount: Optional[int] = Field(None, description="Refinance loan in cents")
    cash_out: Optional[int] = Field(None, description="Cash out in cents")
    current_monthly_cashflow: Optional[int] = Field(None, description="Monthly cashflow in cents")
    annualized_cashflow: Optional[int] = Field(None, description="Annual cashflow in cents")
    timeline: Optional[Dict[str, Any]] = Field(None, description="Timeline details")

    class Config:
        from_attributes = True


class DealLifecycleResponse(BaseModel):
    deal_id: str
    address: str
    status: str
    purchase_price: int
    arv: Optional[int]
    reno_complete: bool
    refinanced: bool
    months_held: Optional[int]
    monthly_cashflow: Optional[int]
