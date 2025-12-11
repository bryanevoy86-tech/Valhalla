"""
PACK SL: Personal Master Dashboard (Life Ops Layer)
Models for daily routines, family snapshots, focus areas, and life tracking
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, UniqueConstraint, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.db import Base


class FocusArea(Base):
    """
    Life focus areas that matter to you.
    Pure organizational structure for life priorities.
    """
    __tablename__ = "focus_areas"

    id = Column(Integer, primary_key=True)
    area_id = Column(String(255), nullable=False, unique=True)
    name = Column(String(255), nullable=False)
    category = Column(String(50), nullable=False)  # health, family, work, education, finance, household
    priority_level = Column(Integer, nullable=False, default=5)  # 1-10
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now())

    # Relationships
    routines = relationship("PersonalRoutine", back_populates="focus_area")


class PersonalRoutine(Base):
    """
    Daily, weekly, or monthly routines.
    Tracks habits and recurring tasks.
    """
    __tablename__ = "personal_routines"

    id = Column(Integer, primary_key=True)
    routine_id = Column(String(255), nullable=False, unique=True)
    focus_area_id = Column(Integer, ForeignKey("focus_areas.id"), nullable=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    frequency = Column(String(50), nullable=False)  # daily, weekly, monthly
    notes = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="active")  # active, paused
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now())

    # Relationships
    focus_area = relationship("FocusArea", back_populates="routines")
    completions = relationship("RoutineCompletion", back_populates="routine")


class RoutineCompletion(Base):
    """
    Track completion of routines over time.
    """
    __tablename__ = "routine_completions"

    id = Column(Integer, primary_key=True)
    completion_id = Column(String(255), nullable=False, unique=True)
    routine_id = Column(Integer, ForeignKey("personal_routines.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    completed = Column(Integer, nullable=False, default=0)  # 0 or 1 (boolean)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    # Relationships
    routine = relationship("PersonalRoutine", back_populates="completions")


class FamilySnapshot(Base):
    """
    Weekly or periodic snapshot of family life.
    User-provided only; no analysis or judgment.
    """
    __tablename__ = "family_snapshots"

    id = Column(Integer, primary_key=True)
    snapshot_id = Column(String(255), nullable=False, unique=True)
    date = Column(DateTime, nullable=False)
    kids_notes = Column(JSON, nullable=True)  # [{name, education, mood, interests}, ...]
    partner_notes = Column(Text, nullable=True)  # user-entered only
    home_operations = Column(Text, nullable=True)  # maintenance, projects, etc.
    highlights = Column(JSON, nullable=True)  # [string, ...]
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now())


class LifeDashboard(Base):
    """
    Weekly life operations dashboard.
    Aggregates routines, habits, wins, and priorities.
    """
    __tablename__ = "life_dashboards"

    id = Column(Integer, primary_key=True)
    dashboard_id = Column(String(255), nullable=False, unique=True)
    week_of = Column(DateTime, nullable=False)  # start of week
    wins = Column(JSON, nullable=True)  # [string, ...]
    challenges = Column(JSON, nullable=True)  # [string, ...]
    habits_tracked = Column(JSON, nullable=True)  # [{habit, completion_rate}, ...]
    upcoming_priorities = Column(JSON, nullable=True)  # [string, ...]
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now())


class PersonalGoal(Base):
    """
    Personal goals with progress tracking.
    """
    __tablename__ = "personal_goals"

    id = Column(Integer, primary_key=True)
    goal_id = Column(String(255), nullable=False, unique=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=False)  # health, education, finance, family, etc.
    deadline = Column(DateTime, nullable=True)
    progress_percent = Column(Integer, nullable=False, default=0)  # 0-100
    status = Column(String(50), nullable=False, default="active")  # active, completed, paused
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now())


class MoodLog(Base):
    """
    Optional mood tracking (user-provided only, no medical data).
    """
    __tablename__ = "mood_logs"

    id = Column(Integer, primary_key=True)
    log_id = Column(String(255), nullable=False, unique=True)
    date = Column(DateTime, nullable=False)
    mood = Column(String(50), nullable=False)  # excellent, good, neutral, challenging, difficult
    energy_level = Column(Integer, nullable=True)  # 1-10
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
