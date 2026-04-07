"""
Children Hub Model - Tracks children family members and their activities
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text
from app.models.base import Base


class ChildrenHub(Base):
    """Central hub for tracking children, their activities, stories, and milestones."""
    __tablename__ = "children_hub"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)
    age = Column(Integer, nullable=True)
    
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
