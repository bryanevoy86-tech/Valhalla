"""
PACK TJ: Kids Education & Development Models
Tracks child profiles, learning plans, and education logs.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.core.db import Base


class ChildProfile(Base):
    __tablename__ = "child_profiles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    age = Column(Integer, nullable=True)
    interests = Column(Text, nullable=True)  # comma- or newline-separated
    notes = Column(Text, nullable=True)

    learning_plans = relationship(
        "LearningPlan", back_populates="child", cascade="all, delete-orphan"
    )
    education_logs = relationship(
        "EducationLog", back_populates="child", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<ChildProfile(name={self.name}, age={self.age})>"


class LearningPlan(Base):
    __tablename__ = "learning_plans"

    id = Column(Integer, primary_key=True, index=True)
    child_id = Column(Integer, ForeignKey("child_profiles.id"), nullable=False)
    timeframe = Column(String, nullable=False)  # daily, weekly, monthly
    goals = Column(Text, nullable=True)         # free-form bullet list
    activities = Column(Text, nullable=True)    # free-form: activity + category
    parent_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    child = relationship("ChildProfile", back_populates="learning_plans")

    def __repr__(self):
        return f"<LearningPlan(timeframe={self.timeframe}, child_id={self.child_id})>"


class EducationLog(Base):
    __tablename__ = "education_logs"

    id = Column(Integer, primary_key=True, index=True)
    child_id = Column(Integer, ForeignKey("child_profiles.id"), nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    completed_activities = Column(Text, nullable=True)
    highlights = Column(Text, nullable=True)
    parent_notes = Column(Text, nullable=True)

    child = relationship("ChildProfile", back_populates="education_logs")

    def __repr__(self):
        return f"<EducationLog(date={self.date}, child_id={self.child_id})>"
