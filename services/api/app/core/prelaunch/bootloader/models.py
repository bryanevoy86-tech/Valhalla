"""PACK-CORE-PRELAUNCH-01: Bootloader - Models"""

from datetime import datetime

from sqlalchemy import Column, DateTime, JSON, String
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.models.base import Base


class BootLog(Base):
    __tablename__ = "boot_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(String(32), nullable=False)  # SUCCESS / PARTIAL / FAILED
    steps = Column(JSON, nullable=True)  # list of {name, status, message}
