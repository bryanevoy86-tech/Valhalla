"""
PACK UE: Maintenance Window & Freeze Switch Models
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from app.models.base import Base


class MaintenanceWindow(Base):
    __tablename__ = "maintenance_windows"

    id = Column(Integer, primary_key=True, index=True)
    starts_at = Column(DateTime, nullable=False)
    ends_at = Column(DateTime, nullable=False)
    description = Column(Text, nullable=True)
    active = Column(Boolean, nullable=False, default=True)


class MaintenanceState(Base):
    """
    Single-row table reflecting current state:
    - normal
    - maintenance
    - read_only
    """
    __tablename__ = "maintenance_state"

    id = Column(Integer, primary_key=True, index=True, default=1)
    mode = Column(String, nullable=False, default="normal")
    reason = Column(Text, nullable=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
