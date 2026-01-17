"""PACK 69: Code Compliance Engine
Checks blueprint logic against regional building codes.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text

from app.models.base import Base


class ComplianceCheck(Base):
    __tablename__ = "compliance_check"

    id = Column(Integer, primary_key=True, index=True)
    blueprint_id = Column(Integer, nullable=False)
    region_code = Column(String, nullable=False)
    violations = Column(Text, nullable=True)
    passed = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
