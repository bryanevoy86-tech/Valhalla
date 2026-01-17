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
    __tablename__ = "governance_decisions"

    id = Column(Integer, primary_key=True, index=True)

    # Subject: what entity is this decision about?
    subject_type = Column(String, nullable=False)  # "deal", "contract", "professional", etc.
    subject_id = Column(Integer, nullable=False)

    # Decision details
    role = Column(String, nullable=False)  # "King", "Queen", "Odin", "Loki", "Tyr", etc.
    action = Column(String, nullable=False)  # "approve", "deny", "override", "flag"
    reason = Column(String, nullable=True)

    # Authority marker
    is_final = Column(Boolean, default=False)

    # Audit trail
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
