"""
PACK ST: Financial Stress Early Warning Engine

Monitors user-defined financial thresholds and surfaces warnings without prediction or diagnosis.
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Boolean, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db import Base


class FinancialIndicator(Base):
    """
    User-defined financial health indicator with threshold.
    
    Attributes:
        indicator_id: Unique identifier
        name: Display name (e.g., "Low Cash Buffer")
        category: Type of indicator [income, expenses, cashflow, savings]
        threshold_type: Direction of threshold [above, below]
        threshold_value: Numeric threshold value
        notes: Additional context
    """
    __tablename__ = "financial_indicators"

    id = Column(Integer, primary_key=True)
    indicator_id = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)  # income, expenses, cashflow, savings
    threshold_type = Column(String(50), nullable=False)  # above, below
    threshold_value = Column(Float, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    stress_events = relationship("FinancialStressEvent", back_populates="indicator", cascade="all, delete-orphan")


class FinancialStressEvent(Base):
    """
    Log of when a financial indicator threshold was triggered.
    
    Attributes:
        event_id: Unique identifier
        indicator_id: FK to FinancialIndicator
        date: When the trigger occurred
        value_at_trigger: The actual value that crossed the threshold
        description: Context about the event
        resolved: Whether this stress has been addressed
        notes: Additional context
    """
    __tablename__ = "financial_stress_events"

    id = Column(Integer, primary_key=True)
    event_id = Column(String(255), unique=True, nullable=False, index=True)
    indicator_id = Column(Integer, ForeignKey("financial_indicators.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    value_at_trigger = Column(Float, nullable=False)
    description = Column(Text, nullable=False)
    resolved = Column(Boolean, nullable=False, server_default="false")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    indicator = relationship("FinancialIndicator", back_populates="stress_events")


class FinancialStressSummary(Base):
    """
    Monthly summary of financial stress and patterns.
    
    Attributes:
        summary_id: Unique identifier
        month: YYYY-MM format
        triggered_indicators: List of indicator IDs that triggered
        patterns: User-observed patterns
        recommendations_to_self: User's own recommendations
        notes: Additional context
    """
    __tablename__ = "financial_stress_summaries"

    id = Column(Integer, primary_key=True)
    summary_id = Column(String(255), unique=True, nullable=False, index=True)
    month = Column(String(7), nullable=False)  # YYYY-MM
    triggered_indicators = Column(JSON, nullable=True)  # List of indicator_id strings
    patterns = Column(JSON, nullable=True)  # User-defined pattern observations
    recommendations_to_self = Column(JSON, nullable=True)  # User's own recommendations
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
