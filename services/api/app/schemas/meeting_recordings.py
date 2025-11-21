from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class MeetingParticipant(BaseModel):
    name: str
    role: Optional[str] = None
    email: Optional[str] = None


class MeetingRecordingCreate(BaseModel):
    source: str  # "lawyer" is main one here
    external_id: Optional[str] = None

    title: Optional[str] = None
    description: Optional[str] = None

    participants: Optional[list[MeetingParticipant]] = None

    raw_transcript: Optional[str] = None
    transcript_json: Optional[dict[str, Any]] = None
    tags: Optional[list[str]] = None

    related_case_id: Optional[UUID] = None
    metadata: Optional[dict[str, Any]] = None


class MeetingRecordingRead(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: datetime

    source: str
    external_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None

    participants: Optional[list[MeetingParticipant]] = None

    raw_transcript: Optional[str] = None
    transcript_json: Optional[dict[str, Any]] = None
    tags: Optional[list[str]] = None

    related_case_id: Optional[UUID] = None
    metadata: Optional[dict[str, Any]] = Field(default=None, validation_alias="metadata_json")

    model_config = {"from_attributes": True}
