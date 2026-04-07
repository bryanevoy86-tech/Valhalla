"""
PACK CI6: Trigger & Threshold Engine Models
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Boolean
from app.models.base import Base


class TriggerRule(Base):
    """
    Condition → action mapping.
    Example:
    - if bankroll_loss_pct > 20% in 7 days → notify + freeze high-risk actions
    """
    __tablename__ = "trigger_rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)  # "finance", "security", "family", etc.
    description = Column(Text, nullable=True)

    condition = Column(JSON, nullable=False)   # structured condition expression
    action = Column(JSON, nullable=False)      # structured action descriptor

    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class TriggerEvent(Base):
    """
    Records when a trigger fired and what it did.
    """
    __tablename__ = "trigger_events"

    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(Integer, nullable=False, index=True)
    status = Column(String, nullable=False)  # "fired", "skipped", "error"
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
