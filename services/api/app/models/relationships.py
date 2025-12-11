"""
PACK TN: Trust & Relationship Mapping Models
Stores relationship profiles and trust history events.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from app.models.base import Base


class RelationshipProfile(Base):
    __tablename__ = "relationship_profiles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    role = Column(String, nullable=True)        # friend, family, contractor, etc.
    relationship_type = Column(String, nullable=True)  # supportive, distant, etc.
    user_trust_level = Column(Float, nullable=True)    # 1–10 user-defined
    boundaries = Column(Text, nullable=True)    # newline-separated
    notes = Column(Text, nullable=True)

    events = relationship(
        "TrustEventLog",
        back_populates="profile",
        cascade="all, delete-orphan",
    )


class TrustEventLog(Base):
    __tablename__ = "trust_event_logs"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("relationship_profiles.id"), nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    event_description = Column(Text, nullable=False)
    trust_change = Column(Float, nullable=True)    # positive or negative
    notes = Column(Text, nullable=True)
    visible = Column(Boolean, default=True)

    profile = relationship("RelationshipProfile", back_populates="events")
