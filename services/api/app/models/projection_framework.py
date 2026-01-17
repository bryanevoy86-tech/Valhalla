"""
PACK SH: Multi-Year Projection Snapshot Framework
Models for storing projection scenarios and tracking expected vs actual
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.db import Base


class ProjectionScenario(Base):
    """
    A named scenario with user-defined assumptions.
    These are NOT automatically calculated — user provides all inputs.
    """
    __tablename__ = "projection_scenarios"

    id = Column(Integer, primary_key=True)
    scenario_id = Column(String(255), nullable=False, unique=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_by = Column(String(255), nullable=True)  # user or source
    assumptions = Column(JSON, nullable=True)  # {income_growth_rate, expense_growth_rate, real_estate_acquisitions, etc.}
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now())

    # Relationships
    years = relationship("ProjectionYear", back_populates="scenario")
    variances = relationship("ProjectionVariance", back_populates="scenario")


class ProjectionYear(Base):
    """
    Yearly expected values for a scenario.
    User provides numbers; Heimdall organizes and tracks them.
    """
    __tablename__ = "projection_years"

    id = Column(Integer, primary_key=True)
    scenario_id = Column(Integer, ForeignKey("projection_scenarios.id"), nullable=False)
    year = Column(Integer, nullable=False)
    expected_income = Column(Integer, nullable=False)  # cents
    expected_expenses = Column(Integer, nullable=False)  # cents
    expected_savings = Column(Integer, nullable=False)  # cents
    expected_cashflow = Column(Integer, nullable=False)  # cents
    expected_net_worth = Column(Integer, nullable=False)  # cents
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now())

    # Unique constraint: one year per scenario
    __table_args__ = (
        UniqueConstraint("scenario_id", "year", name="uq_projection_years_scenario_year"),
    )

    # Relationships
    scenario = relationship("ProjectionScenario", back_populates="years")


class ProjectionVariance(Base):
    """
    Tracks difference between expected and actual for each year.
    User provides actual numbers; Heimdall calculates variance.
    """
    __tablename__ = "projection_variances"

    id = Column(Integer, primary_key=True)
    variance_id = Column(String(255), nullable=False, unique=True)
    scenario_id = Column(Integer, ForeignKey("projection_scenarios.id"), nullable=False)
    year = Column(Integer, nullable=False)
    metric = Column(String(100), nullable=False)  # income, expenses, savings, cashflow, net_worth
    expected = Column(Integer, nullable=False)  # cents
    actual = Column(Integer, nullable=False)  # cents
    difference = Column(Integer, nullable=False)  # actual - expected
    difference_percent = Column(Float, nullable=True)  # (actual - expected) / expected * 100
    explanation = Column(Text, nullable=True)  # user-provided or Heimdall-assisted
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now())

    # Relationships
    scenario = relationship("ProjectionScenario", back_populates="variances")


class ProjectionReport(Base):
    """
    Compiled family-friendly report from a scenario and its actuals.
    """
    __tablename__ = "projection_reports"

    id = Column(Integer, primary_key=True)
    report_id = Column(String(255), nullable=False, unique=True)
    scenario_id = Column(Integer, ForeignKey("projection_scenarios.id"), nullable=False)
    generated_at = Column(DateTime, nullable=False, server_default=func.now())
    summary = Column(JSON, nullable=True)  # {total_expected, total_actual, overall_variance, by_metric: {...}}
    narrative = Column(Text, nullable=True)  # family-friendly explanation
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now())
