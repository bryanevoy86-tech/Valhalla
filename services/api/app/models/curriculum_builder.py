"""PACK 79: Curriculum Builder - Models
Curriculum units and assignments for education delivery.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text

from app.models.base import Base


class CurriculumUnit(Base):
    __tablename__ = "curriculum_unit"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    grade_level = Column(String, nullable=True)
    subject = Column(String, nullable=True)
    content_payload = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AssignedUnit(Base):
    __tablename__ = "assigned_unit"

    id = Column(Integer, primary_key=True, index=True)
    classroom_id = Column(Integer, nullable=False)
    unit_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
