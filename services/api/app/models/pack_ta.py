"""
PACK TA: Trust, Loyalty & Relationship Mapping (Safe, Non-Psychological)

Models for capturing relationship profiles, trust history, and relationship boundaries.
No psychological analysis — only user observations and factual records.
"""

from sqlalchemy import Column, Integer, String, Date, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base


class RelationshipProfile(Base):
    """
    Safe profile of a person in your network with user-defined trust level and boundaries.
    No psychological interpretation — only factual relationships.
    """
    __tablename__ = "relationship_profile"

    id = Column(Integer, primary_key=True)
    profile_id = Column(String(32), unique=True, nullable=False)  # Prefix: relprof
    name = Column(String(255), nullable=False)
    role = Column(String(64), nullable=False)  # friend, family, coworker, contractor, etc.
    relationship_type = Column(String(32), nullable=False)  # supportive, distant, transactional, professional, family
    user_defined_trust_level = Column(Integer, nullable=False)  # 1-10
    boundaries = Column(JSON, nullable=False, default=[])  # User-defined boundaries
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    trust_events = relationship("TrustEventLog", back_populates="profile", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<RelationshipProfile {self.profile_id}: {self.name}>"


class TrustEventLog(Base):
    """
    Records trust-related events without interpretation.
    User specifies impact on trust level.
    """
    __tablename__ = "trust_event_log"

    id = Column(Integer, primary_key=True)
    event_id = Column(String(32), unique=True, nullable=False)  # Prefix: trustevent
    profile_id = Column(Integer, ForeignKey("relationship_profile.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    event_description = Column(Text, nullable=False)
    trust_change = Column(Integer, nullable=False)  # Positive or negative, user-specified
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    profile = relationship("RelationshipProfile", back_populates="trust_events")

    def __repr__(self):
        return f"<TrustEventLog {self.event_id}: {self.date}>"


class RelationshipMapSnapshot(Base):
    """
    Periodic snapshot of all relationships, trust levels, and boundaries.
    """
    __tablename__ = "relationship_map_snapshot"

    id = Column(Integer, primary_key=True)
    snapshot_id = Column(String(32), unique=True, nullable=False)  # Prefix: relsnap
    date = Column(Date, nullable=False)
    key_people = Column(JSON, nullable=False, default=[])  # Names of key people
    trust_levels = Column(JSON, nullable=False, default={})  # {name: trust_level}
    boundaries = Column(JSON, nullable=False, default={})  # {name: [boundaries]}
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<RelationshipMapSnapshot {self.snapshot_id}: {self.date}>"
