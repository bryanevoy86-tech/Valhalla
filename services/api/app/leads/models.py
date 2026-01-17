"""
Lead models for Advanced Lead Scraper (Pack 31).
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from app.core.db import Base


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    email = Column(String(200), nullable=False, index=True)
    phone = Column(String(50), nullable=False)
    status = Column(String(50), default="new", nullable=False)  # new, contacted, qualified, disqualified
    source = Column(String(100), nullable=False)  # e.g., Facebook, referral, LinkedIn
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
