"""
PACK AD: SaaS Access Engine Models
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base


class SaaSPlan(Base):
    __tablename__ = "saas_plans"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, nullable=False, unique=True)  # e.g. "VALHALLA_PRO"
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)

    price_monthly = Column(Float, nullable=True)
    price_yearly = Column(Float, nullable=True)
    currency = Column(String, nullable=False, default="USD")

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    modules = relationship("SaaSPlanModule", back_populates="plan", cascade="all, delete-orphan")
    subscriptions = relationship("Subscription", back_populates="plan")


class SaaSPlanModule(Base):
    __tablename__ = "saas_plan_modules"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("saas_plans.id"), nullable=False)

    # internal feature key, e.g. "arbitrage_engine", "wholesale_engine", "kids_hub"
    module_key = Column(String, nullable=False)

    plan = relationship("SaaSPlan", back_populates="modules")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, nullable=False)
    plan_id = Column(Integer, ForeignKey("saas_plans.id"), nullable=False)

    status = Column(
        String,
        nullable=False,
        default="active",  # active, cancelled, past_due
    )

    # from Stripe or other provider
    provider = Column(String, nullable=True)       # "stripe", "manual", etc.
    provider_sub_id = Column(String, nullable=True)

    started_at = Column(DateTime, default=datetime.utcnow)
    cancelled_at = Column(DateTime, nullable=True)

    plan = relationship("SaaSPlan", back_populates="subscriptions")
