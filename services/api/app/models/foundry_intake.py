"""Durable intake and evidence provenance for scoped Foundry source adapters."""
from sqlalchemy import Column, DateTime, Index, Integer, JSON, String, Uuid

from app.core.db import Base


class FoundryIntakeJob(Base):
    __tablename__ = "prime_foundry_intake_jobs"
    __table_args__ = (Index("ix_foundry_intake_pending", "status", "next_attempt_at"),)

    id = Column(Uuid(), primary_key=True)
    observation_key = Column(String(64), unique=True, nullable=False)
    payload = Column(JSON(), nullable=False)
    digest = Column(String(64), nullable=False)
    status = Column(String(16), nullable=False)
    attempts = Column(Integer(), nullable=False)
    next_attempt_at = Column(DateTime(), nullable=False)
    error_code = Column(String(40))
