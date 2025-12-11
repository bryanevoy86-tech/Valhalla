"""PACK 92: HR Engine - Models"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime

from app.models.base import Base


class Employee(Base):
    __tablename__ = "employee"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    email = Column(String, nullable=False)
    status = Column(String, default="active")  # active, suspended, terminated
    created_at = Column(DateTime, default=datetime.utcnow)


class PerformanceLog(Base):
    __tablename__ = "performance_log"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, nullable=False)
    score = Column(Integer, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class OnboardingDocument(Base):
    __tablename__ = "onboarding_document"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, nullable=False)
    doc_type = Column(String, nullable=False)   # contract, nda, handbook, etc.
    doc_payload = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
