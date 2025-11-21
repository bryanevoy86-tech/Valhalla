from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.db import Base


class GodCase(Base):
    __tablename__ = "god_cases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    title = Column(String(255), nullable=False)
    source_type = Column(String(50), nullable=False, default="generic")
    status = Column(String(50), nullable=False, default="open")

    payload = Column(JSONB, nullable=False)

    heimdall_output = Column(JSONB, nullable=True)
    loki_output = Column(JSONB, nullable=True)
    arbitration_output = Column(JSONB, nullable=True)

    needs_rescan = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
