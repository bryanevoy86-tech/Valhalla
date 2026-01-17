"""
PACK SV: Empire Growth Navigator (Goals → Milestones → Actions Engine)

Organizes long-term goals into milestones and action steps with progress tracking.
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class EmpireGoal(Base):
    """
    High-level empire goal with status and timeframe.
    
    Attributes:
        goal_id: Unique identifier
        name: Goal name
        category: Type [finance, business, family, skills, real_estate, automation]
        description: What this goal encompasses
        timeframe: Duration [short_term, mid_term, long_term]
        status: Current state [not_started, in_progress, completed, paused]
        notes: Additional context
    """
    __tablename__ = "empire_goals"

    id = Column(Integer, primary_key=True)
    goal_id = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)  # finance, business, family, skills, real_estate, automation
    description = Column(Text, nullable=True)
    timeframe = Column(String(50), nullable=False)  # short_term, mid_term, long_term
    status = Column(String(50), nullable=False, server_default="not_started")  # not_started, in_progress, completed, paused
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    milestones = relationship("GoalMilestone", back_populates="goal", cascade="all, delete-orphan")


class GoalMilestone(Base):
    """
    Milestone within a goal with progress tracking.
    
    Attributes:
        milestone_id: Unique identifier
        goal_id: FK to EmpireGoal
        description: What this milestone represents
        due_date: When it should be completed
        progress: 0.0 to 1.0 (user-reported)
        notes: Additional context
    """
    __tablename__ = "goal_milestones"

    id = Column(Integer, primary_key=True)
    milestone_id = Column(String(255), unique=True, nullable=False, index=True)
    goal_id = Column(Integer, ForeignKey("empire_goals.id"), nullable=False)
    description = Column(Text, nullable=False)
    due_date = Column(DateTime, nullable=True)
    progress = Column(Float, nullable=False, server_default="0.0")  # 0.0 - 1.0
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    goal = relationship("EmpireGoal", back_populates="milestones")
    action_steps = relationship("ActionStep", back_populates="milestone", cascade="all, delete-orphan")


class ActionStep(Base):
    """
    Individual action step within a milestone.
    
    Attributes:
        step_id: Unique identifier
        milestone_id: FK to GoalMilestone
        description: What needs to be done
        priority: User-assigned priority (1 = highest)
        status: Current state [pending, in_progress, done]
        notes: Additional context
    """
    __tablename__ = "action_steps"

    id = Column(Integer, primary_key=True)
    step_id = Column(String(255), unique=True, nullable=False, index=True)
    milestone_id = Column(Integer, ForeignKey("goal_milestones.id"), nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(Integer, nullable=False, server_default="1")
    status = Column(String(50), nullable=False, server_default="pending")  # pending, in_progress, done
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    milestone = relationship("GoalMilestone", back_populates="action_steps")
