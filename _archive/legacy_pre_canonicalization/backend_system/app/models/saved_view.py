from sqlalchemy import JSON, TIMESTAMP, Boolean, Column, Integer, String
from sqlalchemy.sql import func

from ..core.db import Base


class SavedView(Base):
    __tablename__ = "saved_views"
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, index=True, nullable=False)
    user_id = Column(Integer, index=True, nullable=False)
    entity = Column(String, nullable=False)
    name = Column(String, nullable=False)
    query = Column(JSON, nullable=False)
    shared = Column(Boolean, default=False, index=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())


class RecentSearch(Base):
    __tablename__ = "recent_searches"
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, index=True, nullable=False)
    user_id = Column(Integer, index=True, nullable=False)
    entity = Column(String, nullable=False)
    query = Column(JSON, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), index=True)
