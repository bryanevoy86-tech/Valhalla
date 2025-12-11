"""
PACK TI: Financial Stress Early Warning Models
Tracks indicators and triggered stress events.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from app.core.db import Base


class FinancialIndicator(Base):
    __tablename__ = "financial_indicators"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=True)  # income, expenses, cashflow, savings
    threshold_type = Column(String, nullable=False)  # above, below
    threshold_value = Column(Float, nullable=False)
    notes = Column(Text, nullable=True)
    active = Column(Boolean, default=True)

    events = relationship("FinancialStressEvent", back_populates="indicator", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<FinancialIndicator(name={self.name}, threshold={self.threshold_value}, active={self.active})>"


class FinancialStressEvent(Base):
    __tablename__ = "financial_stress_events"

    id = Column(Integer, primary_key=True, index=True)
    indicator_id = Column(Integer, ForeignKey("financial_indicators.id"), nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    value_at_trigger = Column(Float, nullable=False)
    description = Column(Text, nullable=True)
    resolved = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)

    indicator = relationship("FinancialIndicator", back_populates="events")

    def __repr__(self):
        return f"<FinancialStressEvent(value={self.value_at_trigger}, resolved={self.resolved})>"
