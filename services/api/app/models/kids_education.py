"""
PACK SM: Kids Education & Development Engine
Models for learning plans, education logs, and child development tracking
"""
from sqlalchemy import String, Integer, Text, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.db import Base


class ChildProfile(Base):
    """Child profile with user-defined skill levels and interests."""
    __tablename__ = 'child_profiles'
    
    id = Integer(primary_key=True)
    child_id = String(255, nullable=False, unique=True)
    name = String(255, nullable=False)
    age = Integer(nullable=False)
    interests = JSON(nullable=True)  # [string]: interests list
    skill_levels = JSON(nullable=True)  # {reading: str, math: str, creativity: str, coordination: str}
    notes = Text(nullable=True)
    created_at = DateTime(nullable=False, server_default=datetime.utcnow)
    updated_at = DateTime(nullable=False, server_default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    learning_plans = relationship('LearningPlan', back_populates='child', foreign_keys='LearningPlan.child_id')
    education_logs = relationship('EducationLog', back_populates='child', foreign_keys='EducationLog.child_id')
    summaries = relationship('ChildSummary', back_populates='child', foreign_keys='ChildSummary.child_id')


class LearningPlan(Base):
    """Customized learning plan with user-defined goals and activities."""
    __tablename__ = 'learning_plans'
    
    id = Integer(primary_key=True)
    plan_id = String(255, nullable=False, unique=True)
    child_id = Integer(ForeignKey('child_profiles.id'), nullable=False)
    timeframe = String(50, nullable=False)  # daily, weekly, monthly
    goals = JSON(nullable=True)  # [{goal: str, notes: str}]
    activities = JSON(nullable=True)  # [{activity: str, category: str, duration_minutes: int}]
    parent_notes = Text(nullable=True)
    status = String(50, nullable=False, server_default='active')  # active, completed, paused
    created_at = DateTime(nullable=False, server_default=datetime.utcnow)
    updated_at = DateTime(nullable=False, server_default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    child = relationship('ChildProfile', back_populates='learning_plans', foreign_keys=[child_id])


class EducationLog(Base):
    """Daily education log tracking completed activities and progress."""
    __tablename__ = 'education_logs'
    
    id = Integer(primary_key=True)
    log_id = String(255, nullable=False, unique=True)
    child_id = Integer(ForeignKey('child_profiles.id'), nullable=False)
    date = DateTime(nullable=False)
    completed_activities = JSON(nullable=True)  # [string]: activities completed
    highlights = JSON(nullable=True)  # [string]: fun/notable moments
    parent_notes = Text(nullable=True)
    created_at = DateTime(nullable=False, server_default=datetime.utcnow)
    
    # Relationships
    child = relationship('ChildProfile', back_populates='education_logs', foreign_keys=[child_id])


class ChildSummary(Base):
    """Weekly education summary with growth notes and next steps."""
    __tablename__ = 'child_summaries'
    
    id = Integer(primary_key=True)
    summary_id = String(255, nullable=False, unique=True)
    child_id = Integer(ForeignKey('child_profiles.id'), nullable=False)
    week_of = DateTime(nullable=False)
    completed_goals = JSON(nullable=True)  # [string]: goals achieved
    fun_moments = JSON(nullable=True)  # [string]: fun/positive experiences
    growth_notes = Text(nullable=True)  # user-supplied observations
    next_week_focus = JSON(nullable=True)  # [string]: areas to focus on
    created_at = DateTime(nullable=False, server_default=datetime.utcnow)
    
    # Relationships
    child = relationship('ChildProfile', back_populates='summaries', foreign_keys=[child_id])
