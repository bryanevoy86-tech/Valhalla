"""
PACK TV: System Log & Audit Trail Models
Central structured log store with correlation IDs.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON

from app.models.base import Base


class SystemLog(Base):
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    level = Column(String, nullable=False, default="INFO", index=True)       # DEBUG, INFO, WARNING, ERROR, CRITICAL
    category = Column(String, nullable=False, default="general", index=True) # auth, security, deal, finance, system, etc.
    message = Column(Text, nullable=False)
    correlation_id = Column(String, nullable=True, index=True)
    user_id = Column(String, nullable=True, index=True)
    context = Column(JSON, nullable=True)
