"""
PACK CI1: Decision Recommendation Engine Models
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Float, Boolean
from app.models.base import Base


class DecisionContextSnapshot(Base):
    """
    A frozen snapshot of the context Heimdall used
    when generating a recommendation (inputs, metrics, mode, etc.).
    """
    __tablename__ = "decision_context_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String, nullable=False)  # "auto", "manual", "heimdall"
    mode = Column(String, nullable=False, default="growth")  # strategic mode
    context_data = Column(JSON, nullable=False)  # arbitrary structured context
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class DecisionRecommendation(Base):
    """
    A specific recommended move, with reasoning and scores.
    """
    __tablename__ = "decision_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    context_id = Column(Integer, nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String, nullable=False)  # "finance", "deal", "health", "family", etc.

    # Scores (0–1 or 0–100 normalized)
    leverage_score = Column(Float, nullable=False, default=0.0)
    risk_score = Column(Float, nullable=False, default=0.0)
    urgency_score = Column(Float, nullable=False, default=0.0)
    alignment_score = Column(Float, nullable=False, default=0.0)

    priority_rank = Column(Integer, nullable=False, default=999)
    recommended = Column(Boolean, nullable=False, default=True)

    reasoning = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
