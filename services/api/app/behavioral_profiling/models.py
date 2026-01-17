"""
Behavioral Profile models for AI Behavioral Profiling (Pack 33).
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.core.db import Base


class BehavioralProfile(Base):
    __tablename__ = "behavioral_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user_profiles.user_id"), nullable=False, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=True, index=True)  # Optional: link to lead
    behavioral_score = Column(Float, nullable=False)  # Engagement score 0-100
    interests = Column(String(500), nullable=True)  # Comma-separated interests
    engagement_level = Column(String(50), default="low")  # low, medium, high
    last_engaged_at = Column(DateTime, nullable=True)  # Last engagement timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<BehavioralProfile(user_id={self.user_id}, score={self.behavioral_score}, level={self.engagement_level})>"
