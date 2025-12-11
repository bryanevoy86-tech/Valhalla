"""
PACK SM: Kids Education & Development Engine
Models for learning plans, education logs, and child development tracking
"""
from sqlalchemy import Column, String, Integer, Text, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from app.models.base import Base


class ChildProfile(Base):
    """Child profile with user-defined skill levels and interests."""
    __tablename__ = 'child_profiles'
    
    id = Column(Integer, primary_key=True)
    child_id = Column(String(255), nullable=False, unique=True)
    name = Column(String(255), nullable=False)
    age = Column(Integer, nullable=False)
    interests = Column(JSON, nullable=True)  # [string]: interests list
    skill_levels = Column(JSON, nullable=True)  # {reading: str, math: str, creativity: str, coordination: str}
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now())
    
    # Relationships
    learning_plans = relationship('LearningPlan', back_populates='child', foreign_keys='LearningPlan.child_id')
    education_logs = relationship('EducationLog', back_populates='child', foreign_keys='EducationLog.child_id')
    summaries = relationship('ChildSummary', back_populates='child', foreign_keys='ChildSummary.child_id')


class LearningPlan(Base):
    """Customized learning plan with user-defined goals and activities."""
    __tablename__ = 'learning_plans'
    
    id = Column(Integer, primary_key=True)
    plan_id = Column(String(255), nullable=False, unique=True)
    child_id = Column(Integer, ForeignKey('child_profiles.id'), nullable=False)
    timeframe = Column(String(50), nullable=False)  # daily, weekly, monthly
    goals = Column(JSON, nullable=True)  # [{goal: str, notes: str}]
    activities = Column(JSON, nullable=True)  # [{activity: str, category: str, duration_minutes: int}]
    parent_notes = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, server_default='active')  # active, completed, paused
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now())
    
    # Relationships
    child = relationship('ChildProfile', back_populates='learning_plans', foreign_keys=[child_id])


class EducationLog(Base):
    """Daily education log tracking completed activities and progress."""
    __tablename__ = 'education_logs'
    
    id = Column(Integer, primary_key=True)
    log_id = Column(String(255), nullable=False, unique=True)
    child_id = Column(Integer, ForeignKey('child_profiles.id'), nullable=False)
    date = Column(DateTime, nullable=False)
    completed_activities = Column(JSON, nullable=True)  # [string]: activities completed
    highlights = Column(JSON, nullable=True)  # [string]: fun/notable moments
    parent_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    
    # Relationships
    child = relationship('ChildProfile', back_populates='education_logs', foreign_keys=[child_id])


class ChildSummary(Base):
    """Weekly education summary with growth notes and next steps."""
    __tablename__ = 'child_summaries'
    
    id = Column(Integer, primary_key=True)
    summary_id = Column(String(255), nullable=False, unique=True)
    child_id = Column(Integer, ForeignKey('child_profiles.id'), nullable=False)
    week_of = Column(DateTime, nullable=False)
    completed_goals = Column(JSON, nullable=True)  # [string]: goals achieved
    fun_moments = Column(JSON, nullable=True)  # [string]: fun/positive experiences
    growth_notes = Column(Text, nullable=True)  # user-supplied observations
    next_week_focus = Column(JSON, nullable=True)  # [string]: areas to focus on
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    
    # Relationships
    child = relationship('ChildProfile', back_populates='summaries', foreign_keys=[child_id])
