"""PACK-CORE-PRELAUNCH-01: Automations Core - Models"""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, JSON, String
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.models.base import Base


class AutomationJob(Base):
    __tablename__ = "automation_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    schedule = Column(String(64), nullable=True)  # cron or simple string
    enabled = Column(Boolean, default=True, nullable=False)

    last_run_at = Column(DateTime, nullable=True)
    last_status = Column(String(32), nullable=True)  # SUCCESS / ERROR / etc.
    last_result = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
