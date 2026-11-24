"""Immutable internal market-source batches scoped to existing Legacy instances."""
from sqlalchemy import Column, DateTime, JSON, String, Uuid
from app.core.db import Base


class MarketEvidence(Base):
    __tablename__ = "prime_market_evidence"

    id = Column(Uuid(), primary_key=True)
    scope_key = Column(String(64), nullable=False, index=True)
    kind = Column(String(12), nullable=False)
    received_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True))
    digest = Column(String(64), nullable=False)
    payload = Column(JSON(), nullable=False)
