"""Durable Stripe ingress and independent processor-balance evidence."""
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, JSON, String, UniqueConstraint, Uuid, func

from app.core.db import Base


class StripeFinancialEvent(Base):
    __tablename__ = "stripe_financial_events"

    event_id = Column(String(128), primary_key=True)
    livemode = Column(Boolean, nullable=False)
    payload_sha256 = Column(String(64), nullable=False)
    snapshot_sha256 = Column(String(64), nullable=False)
    snapshot = Column(JSON, nullable=False)
    received_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class StripeBalanceEvidence(Base):
    __tablename__ = "stripe_balance_evidence"
    __table_args__ = (
        UniqueConstraint("livemode", "balance_transaction_id", name="uq_stripe_balance_transaction"),
        UniqueConstraint("livemode", "payment_intent_id", name="uq_stripe_balance_capture"),
    )

    event_id = Column(String(128), ForeignKey("stripe_financial_events.event_id"), primary_key=True)
    livemode = Column(Boolean, nullable=False)
    payment_intent_id = Column(String(128), nullable=False)
    balance_transaction_id = Column(String(128), nullable=False)
    evidence = Column(JSON, nullable=False)
    evidence_sha256 = Column(String(64), nullable=False)
    observed_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class StripeOrderBinding(Base):
    __tablename__ = "stripe_order_bindings"
    __table_args__ = (
        UniqueConstraint("livemode", "payment_intent_id", name="uq_stripe_order_intent"),
    )

    id = Column(Uuid(), primary_key=True)
    livemode = Column(Boolean, nullable=False)
    payment_intent_id = Column(String(128), nullable=False)
    binding = Column(JSON, nullable=False)
    binding_sha256 = Column(String(64), nullable=False)
