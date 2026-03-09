"""
Adaptive Negotiator models: negotiation strategies.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from app.core.db import Base


class NegotiationStrategy(Base):
    __tablename__ = "negotiation_strategies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)  # e.g., rapport, concession, framing
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
