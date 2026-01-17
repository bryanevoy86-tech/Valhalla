"""
PACK CL9: Decision Outcome Model
Stores the result of important recommendations Heimdall made.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON
from app.models.base import Base


class DecisionOutcome(Base):
    """
    Single decision + outcome record.

    Examples:
    - Heimdall recommended a deal; was it taken? What happened?
    - Heimdall advised against a move; did Bryan override it?
    """

    __tablename__ = "decision_outcomes"

    id = Column(Integer, primary_key=True, index=True)

    # A short machine ID for linking back to the decision context
    decision_id = Column(String, index=True, nullable=False)

    # Human-readable summary of what the decision was about
    title = Column(String, nullable=False)

    # Domain or category: "real_estate", "arbitrage", "family", "security", etc.
    domain = Column(String, nullable=False)

    # "accepted", "ignored", "partial", "blocked", "overridden"
    action_taken = Column(String, nullable=False)

    # "good", "neutral", "bad", or more granular if we want later
    outcome_quality = Column(String, nullable=True)

    # Optional numeric impact score (-100 to +100)
    impact_score = Column(Integer, nullable=True)

    # Free-form notes from Bryan or from Heimdall summary
    notes = Column(Text, nullable=True)

    # Any structured context data (projections, risk bands, etc.)
    context = Column(JSON, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    occurred_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self) -> str:
        return (
            f"<DecisionOutcome(id={self.id}, decision_id={self.decision_id}, "
            f"domain={self.domain}, action_taken={self.action_taken}, "
            f"outcome_quality={self.outcome_quality}, impact_score={self.impact_score})>"
        )
