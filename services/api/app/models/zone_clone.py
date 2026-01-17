"""PACK 94: Zone Replication - Models"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime

from app.models.base import Base


class ZoneReplication(Base):
    __tablename__ = "zone_replication"

    id = Column(Integer, primary_key=True, index=True)
    source_zone_id = Column(Integer, nullable=False)
    target_zone_id = Column(Integer, nullable=False)
    included_modules = Column(Text, nullable=False)   # JSON list
    status = Column(String, default="pending")        # pending, running, complete
    created_at = Column(DateTime, default=datetime.utcnow)
