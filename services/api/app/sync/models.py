from __future__ import annotations
from datetime import datetime
import uuid

from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.db import Base


class SyncStatus(str):
    CLEAN = "clean"
    CONFLICT = "conflict"
    RESOLVED = "resolved"


class GodSyncRecord(Base):
    __tablename__ = "god_sync_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    subject_type = Column(String(100), nullable=False)
    subject_reference = Column(String(200), nullable=True)

    heimdall_payload = Column(JSONB, nullable=True)
    loki_payload = Column(JSONB, nullable=True)

    sync_status = Column(
        String(20), nullable=False,
        default=lambda: SyncStatus.CLEAN
    )

    conflict_summary = Column(Text, nullable=True)
    forwarded_case_id = Column(UUID(as_uuid=True), nullable=True)
