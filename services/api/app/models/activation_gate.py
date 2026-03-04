"""
PACK CL17: Activation Gates + Kill Switch
Defines hard gates that must be green before engines can activate.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON
from app.models.base import Base


class ActivationGate(Base):
    __tablename__ = "activation_gates"

    id = Column(Integer, primary_key=True, index=True)

    gate_key = Column(String, unique=True, index=True, nullable=False)  # e.g. "wholesale_engine"
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    # gate requirements: {"requires":["db_migrations_applied","health_ok"], "min_score":80}
    requirements = Column(JSON, nullable=True)

    # current state
    is_enabled = Column(Boolean, nullable=False, default=False)  # allow engine activation
    is_locked = Column(Boolean, nullable=False, default=False)   # lock prevents any changes
    lock_reason = Column(Text, nullable=True)

    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
