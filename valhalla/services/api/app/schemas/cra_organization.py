"""Schemas for PACK SF: CRA / Tax Interaction Organizational Module"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime


class CRADocumentSchema(BaseModel):
    """CRA document vault schema"""
    doc_id: str = Field(..., description="Unique document identifier")
    year: int = Field(..., description="Tax year")
    category: str = Field(..., description="income, expense, vehicle, grant, supporting_document")
    description: str = Field(..., description="Document description")
    file_url: Optional[str] = Field(None, description="File path")
    file_name: Optional[str] = Field(None, description="File name")
    transaction_id: Optional[str] = Field(None, description="Linked transaction ID")
    vehicle_id: Optional[str] = Field(None, description="Linked vehicle ID")
    notes: Optional[str] = Field(None, description="Additional notes")
    flagged: bool = Field(False, description="Is document flagged")
    flag_reason: Optional[str] = Field(None, description="Reason for flag")
    
    class Config:
        from_attributes = True


class CRASummarySchema(BaseModel):
    """Annual CRA summary schema"""
    summary_id: str = Field(..., description="Unique summary identifier")
    year: int = Field(..., description="Tax year")
    total_income: Optional[float] = Field(None, description="Total income")
    total_business_expenses: Optional[float] = Field(None, description="Total business expenses")
    total_personal_expenses: Optional[float] = Field(None, description="Total personal expenses")
    income_breakdown: Optional[Dict] = Field(None, description="Income by source")
    expense_breakdown: Optional[Dict] = Field(None, description="Expenses by category")
    vehicle_expenses: Optional[float] = Field(None, description="Total vehicle expenses")
    vehicle_kms: Optional[float] = Field(None, description="Total vehicle kilometers")
    flagged_items: Optional[List] = Field(None, description="Flagged items for review")
    unusual_transactions: Optional[List] = Field(None, description="Unusual transactions")
    documentation_gaps: Optional[List] = Field(None, description="Missing documentation")
    questions_for_accountant: Optional[List] = Field(None, description="Questions for accountant")
    supporting_documents: Optional[List] = Field(None, description="Document IDs")
    review_status: str = Field("pending", description="pending, reviewed, filed")
    user_notes: Optional[str] = Field(None, description="User notes")
    accountant_notes: Optional[str] = Field(None, description="Accountant notes")
    
    class Config:
        from_attributes = True


class CRACategoryMapSchema(BaseModel):
    """CRA category mapping schema"""
    category_id: str = Field(..., description="Unique category identifier")
    category: str = Field(..., description="Category name")
    user_defined_description: str = Field(..., description="User description")
    cra_line_reference: Optional[str] = Field(None, description="CRA line reference (informational)")
    example_transactions: Optional[List] = Field(None, description="Example transactions")
    typical_business_use: Optional[str] = Field(None, description="Typical business uses")
    typical_personal_use: Optional[str] = Field(None, description="Typical personal uses")
    notes: Optional[str] = Field(None, description="Category notes")
    
    class Config:
        from_attributes = True


class FiscalYearSnapshotSchema(BaseModel):
    """Fiscal year snapshot schema"""
    snapshot_id: str = Field(..., description="Unique snapshot identifier")
    year: int = Field(..., description="Year")
    fiscal_year_end: datetime = Field(..., description="Fiscal year end date")
    transaction_count: int = Field(0, description="Total transactions")
    total_amount: float = Field(0, description="Total transaction amount")
    documents_count: int = Field(0, description="Total documents")
    documents_by_category: Optional[Dict] = Field(None, description="Documents by category")
    flagged_count: int = Field(0, description="Flagged items count")
    flagged_summary: Optional[Dict] = Field(None, description="Flags by reason")
    recurring_count: int = Field(0, description="Recurring transactions count")
    recurring_list: Optional[List] = Field(None, description="Recurring transactions")
    vehicle_count: int = Field(0, description="Number of vehicles")
    total_vehicle_kms: Optional[float] = Field(None, description="Total vehicle kilometers")
    business_vehicle_percentage: Optional[float] = Field(None, description="Business use percentage")
    gaps_identified: bool = Field(False, description="Are there documentation gaps")
    gap_summary: Optional[str] = Field(None, description="Summary of gaps")
    
    class Config:
        from_attributes = True


class CRAAnnualReportResponse(BaseModel):
    """Annual CRA report response"""
    year: int
    summary: CRASummarySchema
    documents_count: int
    flagged_items_count: int
    unusual_items_count: int
    gaps_count: int
    questions_for_accountant_count: int
    completeness_score: float  # 0-100, based on documentation
    ready_for_filing: bool
