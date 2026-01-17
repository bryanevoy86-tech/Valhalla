"""
PACK TJ: Kids Education & Development Models
Tracks child profiles, learning plans, and education logs.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.core.db import Base


class KidsEducationChildProfile(Base):
    __tablename__ = "child_profiles_tj"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    age = Column(Integer, nullable=True)
    interests = Column(Text, nullable=True)  # comma- or newline-separated
    notes = Column(Text, nullable=True)

    learning_plans = relationship(
        "LearningPlanTJ", back_populates="child", cascade="all, delete-orphan"
    )
    education_logs = relationship(
        "EducationLogTJ", back_populates="child", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<ChildProfile(name={self.name}, age={self.age})>"


class LearningPlanTJ(Base):
    __tablename__ = "learning_plans_tj"

    id = Column(Integer, primary_key=True, index=True)
    child_id = Column(Integer, ForeignKey("child_profiles_tj.id"), nullable=False)
    timeframe = Column(String, nullable=False)  # daily, weekly, monthly
    goals = Column(Text, nullable=True)         # free-form bullet list
    activities = Column(Text, nullable=True)    # free-form: activity + category
    parent_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    child = relationship("KidsEducationChildProfile", back_populates="learning_plans")

    def __repr__(self):
        return f"<LearningPlan(timeframe={self.timeframe}, child_id={self.child_id})>"


class EducationLogTJ(Base):
    __tablename__ = "education_logs_tj"

    id = Column(Integer, primary_key=True, index=True)
    child_id = Column(Integer, ForeignKey("child_profiles_tj.id"), nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    completed_activities = Column(Text, nullable=True)
    highlights = Column(Text, nullable=True)
    parent_notes = Column(Text, nullable=True)

    child = relationship("KidsEducationChildProfile", back_populates="education_logs")

    def __repr__(self):
        return f"<EducationLog(date={self.date}, child_id={self.child_id})>"
