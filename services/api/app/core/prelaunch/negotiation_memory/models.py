"""Negotiation Memory Models"""
from datetime import datetime
from sqlalchemy import Column, DateTime, Float, JSON, String
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.models.base import Base


class NegotiationOutcome(Base):
    """Track negotiation outcomes for learning and adaptation."""
    __tablename__ = "negotiation_outcomes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category = Column(String(64), nullable=False, index=True)  # seller / contractor / lawyer / etc.
    style_used = Column(String(64), nullable=False)
    outcome = Column(String(32), nullable=False)  # WON / LOST / MIXED
    confidence = Column(Float, nullable=True)
    notes = Column(String, nullable=True)
    outcome_metadata = Column(JSON, nullable=True)  # avoid reserved keyword

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
