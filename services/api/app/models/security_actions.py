"""
PACK TR: Security Action Workflow Models
Tracks requested security actions and their approvals.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON

from app.models.base import Base


class SecurityActionRequest(Base):
    __tablename__ = "security_action_requests"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    requested_by = Column(String, nullable=False)  # Heimdall, Tyr, system, human:<id>
    approved_by = Column(String, nullable=True)
    action_type = Column(String, nullable=False)   # block_entity, set_mode, update_policy
    payload = Column(JSON, nullable=True)          # structured details
    status = Column(String, nullable=False, default="pending")  # pending, approved, rejected, executed
    executed_at = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)
