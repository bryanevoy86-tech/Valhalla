"""Governance Engine Models - Policy & Decision Guardrails"""
from datetime import datetime
from sqlalchemy import Column, String, JSON, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.models.base import Base


class PolicyRule(Base):
    """Policy rule governing decisions, risk limits, and CRA constraints."""
    __tablename__ = "policy_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(64), unique=True, nullable=False, index=True)
    description = Column(String, nullable=False)
    conditions = Column(JSON, nullable=False)  # if/then logic
    actions = Column(JSON, nullable=False)  # override, freeze, alert, etc.
    enabled = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
