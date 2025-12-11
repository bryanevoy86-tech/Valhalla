"""
PACK AT: User-Facing Summary Snapshot Models
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text
from app.models.base import Base


class UserSummarySnapshot(Base):
    """Plain language summaries of empire state for family, kids, founders, ops."""
    __tablename__ = "user_summary_snapshots"

    id = Column(Integer, primary_key=True, index=True)

    # what kind of summary: daily, weekly, monthly, milestone, custom
    summary_type = Column(String, nullable=False, default="custom")
    audience = Column(String, nullable=True)   # family, kids, founders, ops, etc.

    title = Column(String, nullable=True)
    body = Column(Text, nullable=False)

    created_by = Column(String, nullable=True)   # heimdall, bryan, lanna
    created_at = Column(DateTime, default=datetime.utcnow)
