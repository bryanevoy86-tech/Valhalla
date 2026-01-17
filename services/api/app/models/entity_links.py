"""
PACK AW: Crosslink / Relationship Graph Models
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from app.models.base import Base


class EntityLink(Base):
    """Unified relationship graph connecting any entity to any other entity."""
    __tablename__ = "entity_links"

    id = Column(Integer, primary_key=True, index=True)

    from_type = Column(String, nullable=False)
    from_id = Column(String, nullable=False)

    to_type = Column(String, nullable=False)
    to_id = Column(String, nullable=False)

    relation = Column(String, nullable=False)  # owns, works_on, parent_of, member_of, etc.

    created_at = Column(DateTime, default=datetime.utcnow)
