"""
PACK SC: Banking & Accounts Structure Planner Models
Safe structural framework for organizing account plans without financial advice
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Float, Boolean
from app.core.db import Base


class BankAccountPlan(Base):
    """
    Represents a planned or active bank account in the user's structure.
    Organizes accounts by purpose and maps to Valhalla income/expense flow.
    """
    __tablename__ = "bank_account_plans"

    id = Column(Integer, primary_key=True, index=True)

    account_id = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)

    # category: operations, payroll, tax_reserve, fun_funds, savings, emergency, personal
    category = Column(String, nullable=False)

    purpose = Column(Text, nullable=False)

    # user-provided institution name
    institution = Column(String, nullable=True)

    # status: planned, open, verified
    status = Column(String, nullable=False, default="planned")

    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True)


class AccountSetupChecklist(Base):
    """
    Tracks the steps needed to open and verify a bank account.
    Non-financial advice, just organizational tracking.
    """
    __tablename__ = "account_setup_checklists"

    id = Column(Integer, primary_key=True, index=True)

    account_plan_id = Column(Integer, nullable=False)  # link to BankAccountPlan

    # items: ID uploaded, incorporation proof, application submitted, account verified, etc.
    step_name = Column(String, nullable=False)
    is_completed = Column(Boolean, default=False)
    documents_required = Column(JSON, nullable=True)  # list of doc types
    uploaded_filename = Column(String, nullable=True)

    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True)


class AccountIncomeMapping(Base):
    """
    Maps income sources and expense categories to specific accounts.
    User-defined routing rules, stored as configuration (not advice).
    """
    __tablename__ = "account_income_mappings"

    id = Column(Integer, primary_key=True, index=True)

    # account being routed to
    target_account_id = Column(Integer, nullable=False)  # link to BankAccountPlan

    # what gets routed
    source_type = Column(String, nullable=False)  # income_source, expense_category, profit, reserve, emergency
    source_name = Column(String, nullable=False)  # specific income source or category

    # percentage or amount
    percentage = Column(Float, nullable=True)  # 0-100
    fixed_amount = Column(Float, nullable=True)

    # is this routing rule active?
    is_active = Column(Boolean, default=True)

    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True)
