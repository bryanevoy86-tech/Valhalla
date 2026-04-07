"""
PACK SU: Personal Safety & Risk Mitigation Planner

Organizes user-defined safety routines, checklists, and contingency plans.
Does NOT give advice, predict danger, or assess risk.
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class SafetyCategory(Base):
    """
    Category of safety concern (e.g., "Travel Safety", "Home Prep").
    
    Attributes:
        category_id: Unique identifier
        name: Display name
        description: What this category covers
    """
    __tablename__ = "safety_categories"

    id = Column(Integer, primary_key=True)
    category_id = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    checklists = relationship("SafetyChecklist", back_populates="category", cascade="all, delete-orphan")
    event_logs = relationship("SafetyEventLog", back_populates="category", cascade="all, delete-orphan")


class SafetyChecklist(Base):
    """
    Individual checklist item for a safety category.
    
    Attributes:
        checklist_id: Unique identifier
        category_id: FK to SafetyCategory
        item: The checklist item/task
        frequency: How often [daily, weekly, before_travel, as_needed]
        notes: Additional instructions
        status: [active, retired]
    """
    __tablename__ = "safety_checklists"

    id = Column(Integer, primary_key=True)
    checklist_id = Column(String(255), unique=True, nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("safety_categories.id"), nullable=False)
    item = Column(String(255), nullable=False)
    frequency = Column(String(50), nullable=False)  # daily, weekly, before_travel, as_needed
    notes = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, server_default="active")  # active, retired
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    category = relationship("SafetyCategory", back_populates="checklists")


class SafetyPlan(Base):
    """
    Contingency plan for a specific situation (user-defined steps only).
    
    Attributes:
        plan_id: Unique identifier
        situation: What scenario this addresses (e.g., "Apartment Fire")
        steps: Ordered steps to follow
        notes: Additional context
    """
    __tablename__ = "safety_plans"

    id = Column(Integer, primary_key=True)
    plan_id = Column(String(255), unique=True, nullable=False, index=True)
    situation = Column(String(255), nullable=False)
    steps = Column(JSON, nullable=True)  # [{"step": str, "order": int}]
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class SafetyEventLog(Base):
    """
    Log of safety-related events and resolutions.
    
    Attributes:
        log_id: Unique identifier
        date: When event occurred
        category_id: FK to SafetyCategory
        event: Description of what happened
        resolution_notes: How it was handled
    """
    __tablename__ = "safety_event_logs"

    id = Column(Integer, primary_key=True)
    log_id = Column(String(255), unique=True, nullable=False, index=True)
    date = Column(DateTime, nullable=False)
    category_id = Column(Integer, ForeignKey("safety_categories.id"), nullable=False)
    event = Column(Text, nullable=False)
    resolution_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    # Relationships
    category = relationship("SafetyCategory", back_populates="event_logs")
