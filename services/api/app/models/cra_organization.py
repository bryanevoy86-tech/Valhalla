"""
PACK SF: CRA / Tax Interaction Organizational Module
Document vault and annual summary organizer.
Does not interpret CRA rules - only organizes and flags.
"""

from sqlalchemy import Column, Integer, String, Float, Text, DateTime, JSON, ForeignKey, func, Boolean
from sqlalchemy.orm import relationship
from app.core.db import Base


class CRADocument(Base):
    """
    CRA document vault - safe storage of supporting documents.
    No interpretation - just organization.
    """
    __tablename__ = "cra_documents"

    id = Column(Integer, primary_key=True)
    doc_id = Column(String(255), unique=True, nullable=False)
    
    year = Column(Integer, nullable=False)
    category = Column(String(100), nullable=False)  # income, expense, vehicle, grant, supporting_document
    
    description = Column(String(255), nullable=False)
    file_url = Column(String(500), nullable=True)  # path to document
    file_name = Column(String(255), nullable=True)
    
    # Reference fields for linking to system
    transaction_id = Column(String(255), nullable=True)  # if linked to spending
    vehicle_id = Column(String(255), nullable=True)  # if vehicle-related
    
    upload_date = Column(DateTime, nullable=False, server_default=func.now())
    notes = Column(Text, nullable=True)
    
    flagged = Column(Boolean, nullable=False, server_default="0")
    flag_reason = Column(String(255), nullable=True)  # e.g., "missing receipt", "incomplete"
    
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now())


class CRASummary(Base):
    """
    Annual summary organized by your rules.
    Flags items for accountant review - no tax determinations.
    """
    __tablename__ = "cra_summaries"

    id = Column(Integer, primary_key=True)
    summary_id = Column(String(255), unique=True, nullable=False)
    
    year = Column(Integer, nullable=False, unique=True)
    
    # Financial totals (you provide these)
    total_income = Column(Float, nullable=True)
    total_business_expenses = Column(Float, nullable=True)
    total_personal_expenses = Column(Float, nullable=True)
    
    # Breakdowns
    income_breakdown = Column(JSON, nullable=True)  # {source: amount}
    expense_breakdown = Column(JSON, nullable=True)  # {category: amount}
    vehicle_expenses = Column(Float, nullable=True)
    vehicle_kms = Column(Float, nullable=True)
    
    # Items flagged for review
    flagged_items = Column(JSON, nullable=True)  # list of flagged transaction summaries
    unusual_transactions = Column(JSON, nullable=True)  # [{date, amount, reason}]
    documentation_gaps = Column(JSON, nullable=True)  # missing receipts, etc.
    
    # Questions for accountant
    questions_for_accountant = Column(JSON, nullable=True)  # [{question, context}]
    
    # Document references
    supporting_documents = Column(JSON, nullable=True)  # [doc_ids]
    
    review_status = Column(String(50), nullable=False, server_default="pending")  # pending, reviewed, filed
    user_notes = Column(Text, nullable=True)
    accountant_notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now())


class CRACategoryMap(Base):
    """
    User-defined category mappings for organizing transactions.
    Neutral organization - no tax implications.
    """
    __tablename__ = "cra_category_maps"

    id = Column(Integer, primary_key=True)
    category_id = Column(String(255), unique=True, nullable=False)
    
    category = Column(String(100), nullable=False)  # e.g., "office_supplies", "vehicle_maint"
    user_defined_description = Column(String(255), nullable=False)
    
    # CRA line reference (informational only)
    cra_line_reference = Column(String(100), nullable=True)  # e.g., "Line 8231"
    
    # Example transactions
    example_transactions = Column(JSON, nullable=True)  # [{desc, amount, date}]
    
    # Typical business uses
    typical_business_use = Column(Text, nullable=True)
    typical_personal_use = Column(Text, nullable=True)
    
    # Organization notes
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now())


class FiscalYearSnapshot(Base):
    """
    Snapshot of fiscal year data for record-keeping and review.
    Pure data organization.
    """
    __tablename__ = "fiscal_year_snapshots"

    id = Column(Integer, primary_key=True)
    snapshot_id = Column(String(255), unique=True, nullable=False)
    
    year = Column(Integer, nullable=False)
    fiscal_year_end = Column(DateTime, nullable=False)  # e.g., Dec 31, 2025
    
    # Transaction summaries
    transaction_count = Column(Integer, nullable=False, server_default="0")
    total_amount = Column(Float, nullable=False, server_default="0")
    
    # Document inventory
    documents_count = Column(Integer, nullable=False, server_default="0")
    documents_by_category = Column(JSON, nullable=True)  # {category: count}
    
    # Flagged items
    flagged_count = Column(Integer, nullable=False, server_default="0")
    flagged_summary = Column(JSON, nullable=True)  # {reason: count}
    
    # Recurring transactions
    recurring_count = Column(Integer, nullable=False, server_default="0")
    recurring_list = Column(JSON, nullable=True)  # recurring transactions identified
    
    # Vehicle usage summary
    vehicle_count = Column(Integer, nullable=False, server_default="0")
    total_vehicle_kms = Column(Float, nullable=True)
    business_vehicle_percentage = Column(Float, nullable=True)
    
    # Completeness check
    gaps_identified = Column(Boolean, nullable=False, server_default=False)
    gap_summary = Column(Text, nullable=True)
    
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now())
