"""
PACK AE: Public Investor Module Models
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from app.models.base import Base


class InvestorProfile(Base):
    __tablename__ = "investor_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, unique=True)

    full_name = Column(String, nullable=True)
    email = Column(String, nullable=True)

    is_accredited = Column(Boolean, default=False)
    country = Column(String, nullable=True)

    strategy_preference = Column(String, nullable=True)  # income, growth, mixed
    risk_tolerance = Column(String, nullable=True)       # conservative, moderate, higher
    notes = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class InvestorProjectSummary(Base):
    """
    High-level, read-only project summary that investors can view.
    No promises, no advice, just neutral description + status.
    """
    __tablename__ = "investor_project_summaries"

    id = Column(Integer, primary_key=True, index=True)

    slug = Column(String, nullable=False, unique=True)
    title = Column(String, nullable=False)
    region = Column(String, nullable=True)
    description = Column(String, nullable=True)

    status = Column(String, nullable=False, default="research")  # research, open, closed
    notes = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
