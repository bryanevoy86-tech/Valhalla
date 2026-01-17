"""Negotiation Engine Models - FREYJA"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.models.base import Base


class NegotiationTemplate(Base):
    """Template for negotiation scripts by category and tone."""
    __tablename__ = "negotiation_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category = Column(String(64), nullable=False, index=True)  # seller, contractor, lawyer, accountant
    tone_profile = Column(String(64), nullable=False)  # assertive, friendly, analytical
    script = Column(JSON, nullable=False)  # entire multi-step script
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)


class NegotiationSession(Base):
    """Record of a negotiation session."""
    __tablename__ = "negotiation_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    target_name = Column(String(128), nullable=True)
    category = Column(String(64), nullable=False, index=True)
    style_used = Column(String(64), nullable=False)
    script_output = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
