from sqlalchemy import JSON, TIMESTAMP, Boolean, Column, Integer, String
from sqlalchemy.sql import func

from .base import Base


class Subscription(Base):
    __tablename__ = "subscriptions"
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, index=True, nullable=False)
    stripe_subscription_id = Column(String, unique=True, index=True, nullable=False)
    status = Column(String, nullable=False)
    plan_key = Column(String, nullable=True)
    items = Column(JSON, nullable=True)
    current_period_end = Column(TIMESTAMP(timezone=True), nullable=True)
    cancel_at_period_end = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), index=True)


class SeatCounter(Base):
    __tablename__ = "seat_counters"
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, unique=True, index=True, nullable=False)
    seats = Column(Integer, nullable=False, default=1)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())


class UsageMeter(Base):
    __tablename__ = "usage_meters"
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, index=True, nullable=False)
    key = Column(String, nullable=False, index=True)
    qty = Column(Integer, nullable=False, default=0)
    window = Column(String, nullable=False, default="daily")
    last_posted_at = Column(TIMESTAMP(timezone=True))
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
