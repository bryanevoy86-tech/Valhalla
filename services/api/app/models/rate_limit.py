"""
PACK UC: Rate Limiting & Quota Engine Models
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from app.models.base import Base


class RateLimitRule(Base):
    __tablename__ = "rate_limit_rules"

    id = Column(Integer, primary_key=True, index=True)
    scope = Column(String, nullable=False)
    key = Column(String, nullable=False)
    window_seconds = Column(Integer, nullable=False, default=60)
    max_requests = Column(Integer, nullable=False, default=60)
    enabled = Column(Boolean, nullable=False, default=True)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class RateLimitSnapshot(Base):
    """
    Optional "last known" snapshot of request counts.
    Implementation of actual counters can be in memory/Redis;
    this table is for audit + rough monitoring only.
    """
    __tablename__ = "rate_limit_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    scope = Column(String, nullable=False)
    key = Column(String, nullable=False)
    window_seconds = Column(Integer, nullable=False)
    max_requests = Column(Integer, nullable=False)
    current_count = Column(Integer, nullable=False, default=0)
    window_started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
