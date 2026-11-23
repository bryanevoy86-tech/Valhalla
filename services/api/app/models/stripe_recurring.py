"""Stripe identifiers and paid service periods for existing SaaS subscriptions."""
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, UniqueConstraint, Uuid

from app.core.db import Base


class StripeSaaSBinding(Base):
    __tablename__ = "stripe_saas_bindings"
    __table_args__ = (
        UniqueConstraint("livemode", "tenant_id", "plan_id", name="uq_stripe_saas_tenant_plan"),
        UniqueConstraint("livemode", "provider_subscription_id", name="uq_stripe_saas_native_subscription"),
    )

    id = Column(Integer, ForeignKey("subscriptions.id"), primary_key=True)
    tenant_id = Column(Uuid(), nullable=False, index=True)
    plan_id = Column(Integer, nullable=False)
    livemode = Column(Boolean, nullable=False)
    binding = Column(JSON, nullable=False)
    binding_sha256 = Column(String(64), nullable=False)
    checkout_started_at = Column(DateTime(timezone=True))
    checkout_session_id = Column(String(128), unique=True)
    provider_subscription_id = Column(String(128))
    cancel_scheduled = Column(Boolean, nullable=False, default=False)


class StripePaidPeriod(Base):
    __tablename__ = "stripe_paid_periods"
    __table_args__ = (
        UniqueConstraint("binding_id", "period_start", name="uq_stripe_paid_period_start"),
    )

    invoice_id = Column(String(128), primary_key=True)
    binding_id = Column(Integer, ForeignKey("stripe_saas_bindings.id"), nullable=False, index=True)
    payment_intent_id = Column(String(128), nullable=False, unique=True)
    period_start = Column(Integer, nullable=False)
    period_end = Column(Integer, nullable=False)
    evidence = Column(JSON, nullable=False)
    evidence_sha256 = Column(String(64), nullable=False)


class StripeRecurringAttempt(Base):
    __tablename__ = "stripe_recurring_attempts"

    event_id = Column(String(128), ForeignKey("stripe_financial_events.event_id"), primary_key=True)
    attempts = Column(Integer, nullable=False, default=0)
    state = Column(String(32), nullable=False)
    retry_at = Column(DateTime(timezone=True))
