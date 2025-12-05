# services/api/app/models/governance_decision.py

from __future__ import annotations

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    func,
)

from app.core.db import Base


class GovernanceDecision(Base):
    """
    Leadership/governance decision records.
    Tracks major decisions by roles (King, Queen, Odin, Loki, Tyr, etc.).
    Pure governance logging - not legal, not binding law.
    """

    __tablename__ = "governance_decisions"

    id = Column(Integer, primary_key=True, index=True)

    subject_type = Column(
        String(50),
        nullable=False
    )  # "deal", "contract", "professional", etc.
    subject_id = Column(Integer, nullable=False)

    role = Column(String(50), nullable=False)  # "King", "Queen", "Odin", "Loki", etc.
    action = Column(
        String(50),
        nullable=False
    )  # "approve", "deny", "override", "flag"
    reason = Column(String(500), nullable=True)

    is_final = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
