"""
PACK SP: Life Event & Crisis Management Engine

Organizes crisis response plans, tracks events, and manages operational readiness
for major life disruptions without psychological diagnosis.
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

from app.models.base import Base


class CrisisProfile(Base):
    """
    Core crisis definition with triggers and severity levels.
    
    Attributes:
        crisis_id: Unique identifier
        name: Crisis name (e.g., "Family Conflict", "Financial Emergency")
        category: Type of crisis [family, health, financial, legal, operations, unexpected]
        triggers: User-defined indicators or events that activate this plan
        severity_levels: Structured levels with descriptions
        notes: Additional context
    """
    __tablename__ = "crisis_profiles"

    id = Column(Integer, primary_key=True)
    crisis_id = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)
    triggers = Column(JSON, nullable=True)  # List of trigger strings
    severity_levels = Column(JSON, nullable=True)  # [{"level": int, "description": str}]
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    action_steps = relationship("CrisisActionStep", back_populates="crisis", cascade="all, delete-orphan")
    log_entries = relationship("CrisisLogEntry", back_populates="crisis", cascade="all, delete-orphan")


class CrisisActionStep(Base):
    """
    Predefined steps executed when a crisis is triggered.
    
    Attributes:
        step_id: Unique identifier
        crisis_id: FK to CrisisProfile
        order: Execution order (1, 2, 3, ...)
        action: What needs to be done (e.g., "Notify lawyer")
        responsible_role: Who executes [King, Queen, Odin, VA, Heimdall]
        notes: Additional instructions
    """
    __tablename__ = "crisis_action_steps"

    id = Column(Integer, primary_key=True)
    step_id = Column(String(255), unique=True, nullable=False, index=True)
    crisis_id = Column(Integer, ForeignKey("crisis_profiles.id"), nullable=False)
    order = Column(Integer, nullable=False)
    action = Column(Text, nullable=False)
    responsible_role = Column(String(100), nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    crisis = relationship("CrisisProfile", back_populates="action_steps")


class CrisisLogEntry(Base):
    """
    Operational log of crisis events and actions taken.
    
    Attributes:
        log_id: Unique identifier
        crisis_id: FK to CrisisProfile
        date: When event occurred
        event: Description of what happened
        actions_taken: List of actions executed
        status: Current state [active, resolved]
        notes: Additional context
    """
    __tablename__ = "crisis_log_entries"

    id = Column(Integer, primary_key=True)
    log_id = Column(String(255), unique=True, nullable=False, index=True)
    crisis_id = Column(Integer, ForeignKey("crisis_profiles.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    event = Column(Text, nullable=False)
    actions_taken = Column(JSON, nullable=True)  # List of action strings
    status = Column(String(50), nullable=False, server_default="active")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    # Relationships
    crisis = relationship("CrisisProfile", back_populates="log_entries")


class CrisisWorkflow(Base):
    """
    Tracks the operational state of a crisis response workflow.
    
    Attributes:
        workflow_id: Unique identifier
        crisis_id: FK to CrisisProfile
        current_step: Which step in the action plan are we on
        status: Workflow state [intake, executing, paused, completed]
        triggered_date: When the crisis was activated
        steps_completed: Count of completed steps
        completion_notes: Final summary when resolved
    """
    __tablename__ = "crisis_workflows"

    id = Column(Integer, primary_key=True)
    workflow_id = Column(String(255), unique=True, nullable=False, index=True)
    crisis_id = Column(String(255), nullable=False)  # Denormalized reference to crisis_id string
    current_step = Column(Integer, nullable=True)
    status = Column(String(50), nullable=False, server_default="intake")  # intake, executing, paused, completed
    triggered_date = Column(DateTime, nullable=True)
    steps_completed = Column(Integer, nullable=False, server_default="0")
    completion_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
