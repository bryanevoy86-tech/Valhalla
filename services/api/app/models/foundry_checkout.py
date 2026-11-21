"""Order and payment evidence for Product Foundry rehearsals."""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Uuid

from app.core.db import Base


class FoundryRehearsalOrder(Base):
    __tablename__ = "prime_foundry_rehearsal_orders"

    id = Column(Uuid(), primary_key=True)
    action_id = Column(String(80), nullable=False)
    listing_sha256 = Column(String(64), nullable=False)
    artifact_id = Column(Uuid(), nullable=False)
    artifact_sha256 = Column(String(64), nullable=False)
    amount_minor = Column(Integer(), nullable=False)
    payment_reference = Column(String(120), unique=True, nullable=False)
    captured_minor = Column(Integer(), nullable=False, default=0)
    refunded_minor = Column(Integer(), nullable=False, default=0)
    delivered_at = Column(DateTime(timezone=True))


class FoundryRehearsalPayment(Base):
    __tablename__ = "prime_foundry_rehearsal_payments"

    event_id = Column(String(120), primary_key=True)
    order_id = Column(Uuid(), ForeignKey("prime_foundry_rehearsal_orders.id"), nullable=False, index=True)
    sha256 = Column(String(64), nullable=False)
    captured_delta = Column(Integer(), nullable=False)
    refunded_delta = Column(Integer(), nullable=False)


class FoundryCampaignVisit(Base):
    __tablename__ = "prime_foundry_campaign_visits"

    id = Column(Uuid(), primary_key=True)
    campaign_id = Column(Integer(), nullable=False, index=True)
    scope_key = Column(String(64), nullable=False)
    order_id = Column(Uuid(), ForeignKey("prime_foundry_rehearsal_orders.id"), unique=True)


class FoundryFixtureSettlement(Base):
    __tablename__ = "prime_foundry_fixture_settlements"

    payment_event_id = Column(String(120), ForeignKey("prime_foundry_rehearsal_payments.event_id"), primary_key=True)
    statement_entry_key = Column(String(64), unique=True, nullable=False)
    statement_id = Column(Uuid(), nullable=False)
    statement_sha256 = Column(String(64), nullable=False)
    payment_sha256 = Column(String(64), nullable=False)
    amount_minor = Column(Integer(), nullable=False)
