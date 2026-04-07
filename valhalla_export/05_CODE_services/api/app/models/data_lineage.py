"""
PACK AM: Data Lineage Engine Model
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, JSON
from app.models.base import Base


class DataLineage(Base):
    __tablename__ = "data_lineage"

    id = Column(Integer, primary_key=True, index=True)

    entity_type = Column(String, nullable=False)    # deal, property, task, child, etc.
    entity_id = Column(String, nullable=False)      # string for flexibility

    action = Column(String, nullable=False)         # created, updated, linked, closed

    source = Column(String, nullable=True)          # heimdall, user, system, automation
    description = Column(String, nullable=True)

    meta_json = Column("metadata", JSON, nullable=True)          # keys changed, tags, timestamps

    created_at = Column(DateTime, default=datetime.utcnow)
