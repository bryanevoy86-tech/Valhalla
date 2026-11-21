"""Versioned evidence for scoped Foundry research."""
from sqlalchemy import Boolean, Column, Date, Index, JSON, String, UniqueConstraint, Uuid

from app.core.db import Base


class FoundryEvidence(Base):
    __tablename__ = "prime_foundry_evidence"
    __table_args__ = (
        UniqueConstraint("scope_key", "source_ref", "observed_on", name="uq_foundry_observation"),
        Index("ix_foundry_evidence_scope", "scope_key", "observed_on"),
    )

    id = Column(Uuid(), primary_key=True)
    scope_key = Column(String(64), nullable=False)
    source_ref = Column(String(240), nullable=False)
    observed_on = Column(Date(), nullable=False)
    expires_on = Column(Date(), nullable=False)
    payload = Column(JSON(), nullable=False)
    digest = Column(String(64), nullable=False)
    revoked = Column(Boolean(), nullable=False, default=False)
