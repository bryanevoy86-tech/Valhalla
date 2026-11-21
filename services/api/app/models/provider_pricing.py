"""Dated provider prices and owner-reconciled staging usage."""
from sqlalchemy import BigInteger, Column, Date, Integer, String, UniqueConstraint, Uuid

from app.core.db import Base


class ProviderPriceQuote(Base):
    __tablename__ = "prime_provider_price_quotes"
    __table_args__ = (UniqueConstraint("provider_id", "vendor", "model", "currency", "effective_on",
                                       name="uq_provider_price_identity_date"),)

    id = Column(Uuid(), primary_key=True)
    provider_id = Column(Integer(), nullable=False)
    vendor = Column(String(40), nullable=False)
    model = Column(String(160), nullable=False)
    source_url = Column(String(300), nullable=False)
    observed_on = Column(Date(), nullable=False)
    effective_on = Column(Date(), nullable=False)
    expires_on = Column(Date(), nullable=False)
    currency = Column(String(3), nullable=False)
    input_minor_per_million = Column(Integer(), nullable=False)
    output_minor_per_million = Column(Integer(), nullable=False)
    sha256 = Column(String(64), nullable=False)


class ProviderUsageReconciliation(Base):
    __tablename__ = "prime_provider_usage_reconciliations"

    probe_id = Column(Uuid(), primary_key=True)
    quote_id = Column(Uuid(), nullable=False)
    statement_ref = Column(String(240), nullable=False)
    estimated_microminor = Column(BigInteger(), nullable=False)
    reported_microminor = Column(BigInteger(), nullable=False)
    usage_sha256 = Column(String(64), nullable=False)
