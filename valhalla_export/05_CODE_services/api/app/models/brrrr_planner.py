"""
PACK SI: Real Estate Acquisition & BRRRR Planner
Models for BRRRR deals, funding plans, cashflow tracking, and refinance scenarios
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.db import Base


class BRRRRDeal(Base):
    """
    Tracks a Buy-Renovate-Rent-Refinance-Repeat deal.
    Pure data organization; no judgment or assumptions.
    """
    __tablename__ = "brrrr_deals"

    id = Column(Integer, primary_key=True)
    deal_id = Column(String(255), nullable=False, unique=True)
    address = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    purchase_price = Column(Integer, nullable=False)  # cents
    reno_budget = Column(Integer, nullable=False)  # cents
    arv = Column(Integer, nullable=True)  # cents; user provides after analyzing comps
    strategy_notes = Column(Text, nullable=True)
    acquisition_date = Column(DateTime, nullable=True)
    reno_start_date = Column(DateTime, nullable=True)
    reno_end_date = Column(DateTime, nullable=True)
    refinance_date = Column(DateTime, nullable=True)
    status = Column(String(50), nullable=False, default="analysis")  # analysis, in_progress, refinanced, holding
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now())

    # Relationships
    funding_plan = relationship("BRRRRFundingPlan", back_populates="deal", uselist=False)
    cashflow_entries = relationship("BRRRRCashflowEntry", back_populates="deal")
    refinance_snapshots = relationship("BRRRRRefinanceSnapshot", back_populates="deal")


class BRRRRFundingPlan(Base):
    """
    User-provided funding strategy for a deal.
    No calculations; pure organizational structure.
    """
    __tablename__ = "brrrr_funding_plans"

    id = Column(Integer, primary_key=True)
    plan_id = Column(String(255), nullable=False, unique=True)
    deal_id = Column(Integer, ForeignKey("brrrr_deals.id"), nullable=False)
    down_payment = Column(Integer, nullable=False)  # cents
    renovation_funds_source = Column(String(255), nullable=True)  # hard money, private lender, cash, etc.
    holding_costs_plan = Column(String(255), nullable=True)  # how reno costs are covered
    refinance_strategy = Column(Text, nullable=True)  # user's plan for refi
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now())

    # Relationships
    deal = relationship("BRRRRDeal", back_populates="funding_plan")


class BRRRRCashflowEntry(Base):
    """
    Monthly or periodic cashflow tracking during hold phase.
    User logs rent, expenses, net; system organizes.
    """
    __tablename__ = "brrrr_cashflow_entries"

    id = Column(Integer, primary_key=True)
    entry_id = Column(String(255), nullable=False, unique=True)
    deal_id = Column(Integer, ForeignKey("brrrr_deals.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    rent = Column(Integer, nullable=False)  # cents
    expenses = Column(Integer, nullable=False)  # cents
    net = Column(Integer, nullable=False)  # cents (rent - expenses)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now())

    # Relationships
    deal = relationship("BRRRRDeal", back_populates="cashflow_entries")


class BRRRRRefinanceSnapshot(Base):
    """
    Records refinance results and cash-out amounts.
    User provides actual loan terms and results.
    """
    __tablename__ = "brrrr_refinance_snapshots"

    id = Column(Integer, primary_key=True)
    snapshot_id = Column(String(255), nullable=False, unique=True)
    deal_id = Column(Integer, ForeignKey("brrrr_deals.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    new_loan_amount = Column(Integer, nullable=False)  # cents
    interest_rate = Column(Float, nullable=False)
    loan_term_months = Column(Integer, nullable=True)
    cash_out_amount = Column(Integer, nullable=False)  # cents
    new_payment = Column(Integer, nullable=False)  # cents per month
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now())

    # Relationships
    deal = relationship("BRRRRDeal", back_populates="refinance_snapshots")


class BRRRRSummary(Base):
    """
    Compiled summary of BRRRR deal lifecycle and outcomes.
    Aggregates purchase, reno, refinance, and hold metrics.
    """
    __tablename__ = "brrrr_summaries"

    id = Column(Integer, primary_key=True)
    summary_id = Column(String(255), nullable=False, unique=True)
    deal_id = Column(Integer, ForeignKey("brrrr_deals.id"), nullable=False)
    purchase_price = Column(Integer, nullable=False)  # cents
    reno_actual = Column(Integer, nullable=True)  # cents
    reno_budget = Column(Integer, nullable=True)  # cents
    arv = Column(Integer, nullable=True)  # cents
    initial_equity = Column(Integer, nullable=True)  # cents
    refi_loan_amount = Column(Integer, nullable=True)  # cents
    cash_out = Column(Integer, nullable=True)  # cents
    current_monthly_cashflow = Column(Integer, nullable=True)  # cents
    annualized_cashflow = Column(Integer, nullable=True)  # cents
    timeline = Column(JSON, nullable=True)  # {acquisition_date, reno_duration, hold_months, etc.}
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now())
