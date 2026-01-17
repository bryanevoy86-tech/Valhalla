from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.db import Base


class Dispute(Base):
    """
    Tracks disagreement between:
    - human specialist(s)
    - Heimdall
    - Loki

    and the lifecycle of resolving that disagreement.
    """

    __tablename__ = "disputes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    case_id = Column(UUID(as_uuid=True), nullable=False)

    human_role = Column(String(30), nullable=True)
    human_specialist_id = Column(UUID(as_uuid=True), nullable=True)

    topic = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)

    human_position = Column(JSONB, nullable=True)
    heimdall_position = Column(JSONB, nullable=True)
    loki_position = Column(JSONB, nullable=True)

    status = Column(String(30), nullable=False, default="open")

    resolution_summary = Column(Text, nullable=True)
    resolution_metadata = Column(JSONB, nullable=True)
