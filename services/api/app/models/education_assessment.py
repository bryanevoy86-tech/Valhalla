"""PACK 80: Education SaaS - Assessment Models
Assignments, submissions, and grades for tracking student work.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Float

from app.models.base import Base


class Assignment(Base):
    __tablename__ = "assignment"

    id = Column(Integer, primary_key=True, index=True)
    classroom_id = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    instructions = Column(Text, nullable=False)
    due_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Submission(Base):
    __tablename__ = "submission"

    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, nullable=False)
    student_id = Column(Integer, nullable=False)
    content_payload = Column(Text, nullable=False)
    submitted_at = Column(DateTime, default=datetime.utcnow)


class Grade(Base):
    __tablename__ = "grade"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, nullable=False)
    score = Column(Float, nullable=False)
    feedback = Column(Text, nullable=True)
    graded_at = Column(DateTime, default=datetime.utcnow)
