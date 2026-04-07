"""
PACK SQ: Partner / Marriage Stability Ops Module

Practical life logistics for shared responsibilities, communication, and household operations.
NON-PSYCHOLOGICAL - no emotional analysis, judgment, or relationship diagnosis.
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class RelationshipOpsProfile(Base):
    """
    Operational framework for partner/marriage logistics.
    
    Attributes:
        profile_id: Unique identifier
        partner_name: Name of partner
        shared_domains: Areas of shared responsibility with primary/secondary owners
        communication_protocol: How to communicate about specific topics
        boundaries: User-defined practical boundaries
        notes: Additional context
    """
    __tablename__ = "relationship_ops_profiles"

    id = Column(Integer, primary_key=True)
    profile_id = Column(String(255), unique=True, nullable=False, index=True)
    partner_name = Column(String(255), nullable=False)
    shared_domains = Column(JSON, nullable=True)  # [{"domain": str, "primary_responsible": str, "secondary_responsible": str}]
    communication_protocol = Column(JSON, nullable=True)  # [{"context": str, "preferred_method": str, "notes": str}]
    boundaries = Column(JSON, nullable=True)  # List of boundary strings
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    coparenting_schedules = relationship("CoParentingSchedule", back_populates="profile", cascade="all, delete-orphan")
    household_responsibilities = relationship("HouseholdResponsibility", back_populates="profile", cascade="all, delete-orphan")
    communication_logs = relationship("CommunicationLog", back_populates="profile", cascade="all, delete-orphan")


class CoParentingSchedule(Base):
    """
    Personal scheduling tool for co-parenting responsibilities.
    NOT legal custody logic — just operational scheduling.
    
    Attributes:
        schedule_id: Unique identifier
        profile_id: FK to RelationshipOpsProfile
        days: Weekly schedule with responsible parent, pickup/dropoff times
        special_rules: Holidays, school events, shared tasks
        notes: Additional context
    """
    __tablename__ = "coparenting_schedules"

    id = Column(Integer, primary_key=True)
    schedule_id = Column(String(255), unique=True, nullable=False, index=True)
    profile_id = Column(Integer, ForeignKey("relationship_ops_profiles.id"), nullable=False)
    days = Column(JSON, nullable=True)  # [{"day": str, "responsible_parent": str, "pickup_time": str, "dropoff_time": str}]
    special_rules = Column(JSON, nullable=True)  # List of rule strings
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    profile = relationship("RelationshipOpsProfile", back_populates="coparenting_schedules")


class HouseholdResponsibility(Base):
    """
    Task assignment and tracking for household operations.
    
    Attributes:
        task_id: Unique identifier
        profile_id: FK to RelationshipOpsProfile
        task: What needs to be done
        frequency: How often [daily, weekly, monthly, as_needed]
        primary_responsible: Primary owner
        fallback_responsible: Backup owner if primary unavailable
        notes: Additional context
    """
    __tablename__ = "household_responsibilities"

    id = Column(Integer, primary_key=True)
    task_id = Column(String(255), unique=True, nullable=False, index=True)
    profile_id = Column(Integer, ForeignKey("relationship_ops_profiles.id"), nullable=False)
    task = Column(String(255), nullable=False)
    frequency = Column(String(50), nullable=False)  # daily, weekly, monthly, as_needed
    primary_responsible = Column(String(255), nullable=False)
    fallback_responsible = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    profile = relationship("RelationshipOpsProfile", back_populates="household_responsibilities")


class CommunicationLog(Base):
    """
    Structured record of important conversations (user-entered).
    Helps Heimdall structure next-step plans without judgment or interpretation.
    
    Attributes:
        log_id: Unique identifier
        profile_id: FK to RelationshipOpsProfile
        date: When conversation occurred
        topic: What was discussed
        summary: What was said/decided
        follow_up_required: Whether action is needed
        notes: Additional context
    """
    __tablename__ = "communication_logs"

    id = Column(Integer, primary_key=True)
    log_id = Column(String(255), unique=True, nullable=False, index=True)
    profile_id = Column(Integer, ForeignKey("relationship_ops_profiles.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    topic = Column(String(255), nullable=False)
    summary = Column(Text, nullable=True)
    follow_up_required = Column(Boolean, nullable=False, server_default="false")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    # Relationships
    profile = relationship("RelationshipOpsProfile", back_populates="communication_logs")
