"""
PACK SC: Banking & Accounts Structure Planner Schemas
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class BankAccountPlanSchema(BaseModel):
    account_id: str
    name: str
    category: str = Field(..., description="operations, payroll, tax_reserve, fun_funds, savings, emergency, personal")
    purpose: str
    institution: Optional[str] = None
    status: str = Field(default="planned")
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class AccountSetupChecklistSchema(BaseModel):
    account_plan_id: int
    step_name: str
    is_completed: bool = False
    documents_required: Optional[List[str]] = None
    uploaded_filename: Optional[str] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class AccountIncomeMappingSchema(BaseModel):
    target_account_id: int
    source_type: str = Field(..., description="income_source, expense_category, profit, reserve, emergency")
    source_name: str
    percentage: Optional[float] = None
    fixed_amount: Optional[float] = None
    is_active: bool = True
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class AccountStructureSummaryResponse(BaseModel):
    total_accounts: int
    accounts_by_category: Dict[str, int]
    total_mappings: int
    active_mappings: int
    accounts_ready_for_use: int
