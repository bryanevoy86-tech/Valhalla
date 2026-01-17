from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.db import Base


class SpecialistFeedback(Base):
    __tablename__ = "specialist_feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    god_case_id = Column(
        UUID(as_uuid=True), ForeignKey("god_cases.id", ondelete="CASCADE"), nullable=False, index=True
    )

    specialist_role = Column(String(50), nullable=False)
    specialist_name = Column(String(255), nullable=True)
    notes = Column(Text, nullable=False)
    suggested_changes = Column(JSONB, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
