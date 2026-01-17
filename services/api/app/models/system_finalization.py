"""PACK 60: System Finalization
System integrity sealing mechanism for deployment finalization.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean

from app.models.base import Base


class SystemIntegritySeal(Base):
    __tablename__ = "system_integrity_seal"

    id = Column(Integer, primary_key=True, index=True)
    seal_hash = Column(String, nullable=False)
    schema_version = Column(String, nullable=False)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
