from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.db import Base


class MeetingRecording(Base):
    __tablename__ = "meeting_recordings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # who / what this meeting is with
    source = Column(String(50), nullable=False)  # "lawyer" | "accountant" | "advisor" | "other"
    external_id = Column(String(200), nullable=True)  # e.g. Zoom ID, file ID

    title = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)

    # who was on the call
    participants = Column(JSONB, nullable=True)  # list of {name, role, email?}

    # transcript and AI-enriched data
    raw_transcript = Column(Text, nullable=True)
    transcript_json = Column(JSONB, nullable=True)  # segmented transcript, timestamps, etc.
    tags = Column(JSONB, nullable=True)  # ["trust", "tax", "contract", ...]

    # link to a dual-god case, if applicable
    related_case_id = Column(UUID(as_uuid=True), nullable=True)

    # extra structured info (e.g., summary, actions)
    metadata_json = Column("metadata", JSONB, nullable=True)
