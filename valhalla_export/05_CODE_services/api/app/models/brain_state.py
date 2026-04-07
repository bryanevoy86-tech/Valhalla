"""
PACK AL: Brain State Snapshot Models
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text
from app.models.base import Base


class BrainStateSnapshot(Base):
    __tablename__ = "brain_state_snapshots"

    id = Column(Integer, primary_key=True, index=True)

    label = Column(String, nullable=True)  # e.g. "post-deploy check", "pre-experiment"

    # JSON strings storing snapshots
    empire_dashboard_json = Column(Text, nullable=True)
    analytics_snapshot_json = Column(Text, nullable=True)
    scenarios_summary_json = Column(Text, nullable=True)

    created_by = Column(String, nullable=True)  # heimdall, user, worker
    created_at = Column(DateTime, default=datetime.utcnow)
