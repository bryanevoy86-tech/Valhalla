"""PACK 66: Release Preparation & System Hardening
Tracks version rollouts and deployment signatures.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime

from app.models.base import Base


class SystemRelease(Base):
    __tablename__ = "system_release"

    id = Column(Integer, primary_key=True, index=True)
    version = Column(String, nullable=False)
    changelog = Column(String, nullable=False)
    deployed_by = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
