"""
PACK SG: Income Routing & Separation Engine
Models for income flow routing, allocation rules, and separation of funds
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.db import Base


class IncomeRouteRule(Base):
    """
    Define routing rules for income allocation.
    User provides all logic; system executes rules without judgment.
    """
    __tablename__ = "income_route_rules"

    id = Column(Integer, primary_key=True)
    rule_id = Column(String(255), nullable=False, unique=True)
    source = Column(String(255), nullable=False)  # job, business, side income, rental, etc.
    description = Column(Text, nullable=True)
    allocation_type = Column(String(50), nullable=False)  # "percent" or "fixed"
    allocation_value = Column(Float, nullable=False)  # % or fixed amount
    target_account = Column(String(255), nullable=False)  # account from banking planner
    notes = Column(Text, nullable=True)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now())

    # Relationships
    income_events = relationship("IncomeEvent", back_populates="rule")
    routing_logs = relationship("IncomeRoutingLog", back_populates="rule")


class IncomeEvent(Base):
    """
    Neutral logging of income arrivals.
    No judgment, calculation, or advice — pure data capture.
    """
    __tablename__ = "income_events"

    id = Column(Integer, primary_key=True)
    event_id = Column(String(255), nullable=False, unique=True)
    date = Column(DateTime, nullable=False)
    source = Column(String(255), nullable=False)  # matches rule source
    amount = Column(Integer, nullable=False)  # cents
    notes = Column(Text, nullable=True)
    routed = Column(Boolean, nullable=False, default=False)
    route_rule_id = Column(Integer, ForeignKey("income_route_rules.id"), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now())

    # Relationships
    rule = relationship("IncomeRouteRule", back_populates="income_events")


class IncomeRoutingLog(Base):
    """
    Log of routing execution for audit and tracking.
    Records what was calculated, what user approved, what was executed.
    """
    __tablename__ = "income_routing_logs"

    id = Column(Integer, primary_key=True)
    log_id = Column(String(255), nullable=False, unique=True)
    rule_id = Column(Integer, ForeignKey("income_route_rules.id"), nullable=False)
    income_event_id = Column(String(255), nullable=False)
    calculated_amount = Column(Integer, nullable=False)  # cents
    target_account = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, default="pending")  # pending, approved, executed, rejected
    user_approval_date = Column(DateTime, nullable=True)
    execution_date = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now())

    # Relationships
    rule = relationship("IncomeRouteRule", back_populates="routing_logs")


class IncomeRoutingSummary(Base):
    """
    Snapshot of income allocation for a specific date/event.
    Shows what Heimdall calculated and is proposing.
    """
    __tablename__ = "income_routing_summaries"

    id = Column(Integer, primary_key=True)
    summary_id = Column(String(255), nullable=False, unique=True)
    date = Column(DateTime, nullable=False)
    total_income = Column(Integer, nullable=False)  # cents
    allocations = Column(JSON, nullable=True)  # [{account, amount, percent}, ...]
    unallocated_balance = Column(Integer, nullable=False, default=0)  # cents
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now())
