"""PACK 77: Education SaaS - Org Models
School, classroom, and teacher profiles.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text

from app.models.base import Base


class School(Base):
    __tablename__ = "school"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    district = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Classroom(Base):
    __tablename__ = "classroom"

    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    grade_level = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Teacher(Base):
    __tablename__ = "teacher"

    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    subject = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
