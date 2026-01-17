from sqlalchemy import JSON, TIMESTAMP, Boolean, Column, Integer, String
from sqlalchemy.sql import func

from ..core.db import Base


class SavedChart(Base):
    __tablename__ = "saved_charts"
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, index=True, nullable=False)
    user_id = Column(Integer, index=True, nullable=False)
    name = Column(String, nullable=False)
    viz = Column(String, nullable=False, default="line")
    spec = Column(JSON, nullable=False)
    shared = Column(Boolean, default=False, index=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())


class Dashboard(Base):
    __tablename__ = "dashboards"
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, index=True, nullable=False)
    user_id = Column(Integer, index=True, nullable=False)
    name = Column(String, nullable=False)
    layout = Column(JSON, nullable=False, default=list)
    shared = Column(Boolean, default=False, index=True)
