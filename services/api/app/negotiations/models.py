"""
Negotiation models.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from datetime import datetime
from app.core.db import Base

class Negotiation(Base):
    __tablename__ = 'negotiations'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('user_profiles.user_id', ondelete='CASCADE'), nullable=False, index=True)
    deal_id = Column(Integer, nullable=True, index=True)  # optional foreign key to a deals table if present
    tone_score = Column(Float, nullable=False)
    sentiment_score = Column(Float, nullable=False)
    negotiation_stage = Column(String, nullable=False, default='initial')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
