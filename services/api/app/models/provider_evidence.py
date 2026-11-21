"""Version-bound comparison evidence for registered models."""
from sqlalchemy import Column, DateTime, Integer, JSON, String, Uuid

from app.core.db import Base


class ProviderEvidence(Base):
    __tablename__ = "prime_provider_evidence"
    id = Column(Uuid(), primary_key=True)
    provider_id = Column(Integer(), nullable=False, index=True)
    vendor = Column(String(40), nullable=False)
    model = Column(String(160), nullable=False)
    role = Column(String(40), nullable=False)
    suite_version = Column(Integer(), nullable=False)
    input_digest = Column(String(64), nullable=False)
    fixture_results = Column(JSON(), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
