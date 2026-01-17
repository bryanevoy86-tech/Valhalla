"""PACK 78: Education SaaS - Student Models
Student profiles and parent account management.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text

from app.models.base import Base


class Student(Base):
    __tablename__ = "student"

    id = Column(Integer, primary_key=True, index=True)
    classroom_id = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    age = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ParentAccount(Base):
    __tablename__ = "parent_account"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, nullable=False)
    parent_name = Column(String, nullable=False)
    contact_email = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
