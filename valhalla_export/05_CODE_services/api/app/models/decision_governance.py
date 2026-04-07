"""
PACK AP: Decision Governance Engine Models
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON
from app.models.base import Base


class DecisionPolicy(Base):
    """
    Defines what kind of decisions exist and what is required to approve them.
    """
    __tablename__ = "decision_policies"

    id = Column(Integer, primary_key=True, index=True)

    key = Column(String, nullable=False, unique=True)   # e.g. "approve_deal", "hire_professional"
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)

    # who is allowed to make this decision (role names, comma-separated)
    allowed_roles = Column(String, nullable=True)       # e.g. "king,queen,odin"

    # whether multiple reviewers or approvals are required
    min_approvals = Column(Integer, nullable=False, default=1)

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)


class DecisionRecord(Base):
    """
    A concrete decision attempt (approved or rejected).
    """
    __tablename__ = "decision_records"

    id = Column(Integer, primary_key=True, index=True)

    policy_key = Column(String, nullable=False)         # link to DecisionPolicy.key
    entity_type = Column(String, nullable=False)        # deal, retainer, contract, etc.
    entity_id = Column(String, nullable=False)

    # who initiated: user id, role, or "heimdall"
    initiator = Column(String, nullable=False)
    initiator_role = Column(String, nullable=True)

    status = Column(
        String,
        nullable=False,
        default="pending",   # pending, approved, rejected
    )

    # optional reason / context payload
    context = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    decided_at = Column(DateTime, nullable=True)
