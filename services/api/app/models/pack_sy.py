"""
PACK SY: Strategic Decision History & Reason Archive

Models for capturing strategic decisions, revisions, and decision chains.
This creates the reasoning spine of Valhalla, allowing Heimdall to understand
your logic, past constraints, and evolution of strategy.
"""

from sqlalchemy import Column, Integer, String, Date, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base


class StrategicDecision(Base):
    """
    Records a strategic decision with reasoning, alternatives considered, and constraints.
    """
    __tablename__ = "strategic_decision"

    id = Column(Integer, primary_key=True)
    decision_id = Column(String(32), unique=True, nullable=False)  # Prefix: strdec
    date = Column(Date, nullable=False)
    title = Column(String(255), nullable=False)
    category = Column(String(32), nullable=False)  # business, family, finance, real_estate, system
    reasoning = Column(Text, nullable=False)  # User-stated rationale
    alternatives_considered = Column(JSON, nullable=False, default=[])  # List of alternatives
    constraints = Column(JSON, nullable=False, default=[])  # Constraints at time of decision
    expected_outcome = Column(Text, nullable=False)  # What you expected to happen
    status = Column(String(16), nullable=False, default="active")  # active, revised, reversed, completed
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    revisions = relationship("DecisionRevision", back_populates="decision", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<StrategicDecision {self.decision_id}: {self.title}>"


class DecisionRevision(Base):
    """
    Records when and why a decision was revised, changed direction, or reversed.
    """
    __tablename__ = "decision_revision"

    id = Column(Integer, primary_key=True)
    revision_id = Column(String(32), unique=True, nullable=False)  # Prefix: decrev
    decision_id = Column(Integer, ForeignKey("strategic_decision.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    reason_for_revision = Column(Text, nullable=False)  # Why you changed course
    what_changed = Column(Text, nullable=False)  # What specifically changed
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    decision = relationship("StrategicDecision", back_populates="revisions")

    def __repr__(self):
        return f"<DecisionRevision {self.revision_id}: {self.date}>"


class DecisionChainSnapshot(Base):
    """
    Periodic snapshot of major decisions, how they evolved, and their collective impact.
    """
    __tablename__ = "decision_chain_snapshot"

    id = Column(Integer, primary_key=True)
    snapshot_id = Column(String(32), unique=True, nullable=False)  # Prefix: decsnap
    date = Column(Date, nullable=False)
    major_decisions = Column(JSON, nullable=False, default=[])  # Key decision IDs/titles
    revisions = Column(JSON, nullable=False, default=[])  # What evolved and when
    reasons = Column(JSON, nullable=False, default=[])  # User-stated reasons for changes
    system_impacts = Column(JSON, nullable=False, default=[])  # How decisions affected empire
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<DecisionChainSnapshot {self.snapshot_id}: {self.date}>"
