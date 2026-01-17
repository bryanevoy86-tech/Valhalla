from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.db import Base


class GodVerdict(Base):
    __tablename__ = "god_verdicts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    case_id = Column(UUID(as_uuid=True), nullable=False)

    trigger = Column(String(50), nullable=True)

    heimdall_summary = Column(Text, nullable=True)
    heimdall_recommendation = Column(JSONB, nullable=True)
    heimdall_confidence = Column(String(20), nullable=True)

    loki_summary = Column(Text, nullable=True)
    loki_recommendation = Column(JSONB, nullable=True)
    loki_confidence = Column(String(20), nullable=True)

    consensus = Column(String(20), nullable=True)
    risk_level = Column(String(20), nullable=True)

    notes = Column(Text, nullable=True)
    metadata_json = Column("metadata", JSONB, nullable=True)
