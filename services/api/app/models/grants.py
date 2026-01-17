"""
Grant sources and records models for tracking funding opportunities.
"""

from sqlalchemy import Column, Integer, String, Text, Date, Boolean, ForeignKey, Numeric, DateTime, func
from sqlalchemy.orm import relationship
from ..core.db import Base


class GrantSource(Base):
    __tablename__ = "grant_sources"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(160), nullable=False)
    url = Column(Text, nullable=True)
    region = Column(String(80), nullable=True)        # e.g., "CA-MB", "CA", "US"
    tags = Column(String(255), nullable=True)         # comma list
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class GrantRecord(Base):
    __tablename__ = "grant_records"
    
    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey("grant_sources.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(240), nullable=False)
    program = Column(String(160), nullable=True)
    category = Column(String(120), nullable=True)     # e.g., "startup","training","innovation"
    region = Column(String(80), nullable=True)
    amount_min = Column(Numeric(18,2), nullable=True)
    amount_max = Column(Numeric(18,2), nullable=True)
    deadline = Column(Date, nullable=True)
    link = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    score_json = Column(Text, nullable=True)          # store computed scoring detail
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    source = relationship("GrantSource", lazy="joined")
