from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.meeting_recordings import MeetingRecording
from app.schemas.meeting_recordings import (
    MeetingRecordingCreate,
    MeetingRecordingRead,
)

router = APIRouter(prefix="/lawyer-feed", tags=["Lawyer AI Feed"])


@router.post("/recordings", response_model=MeetingRecordingRead)
def create_lawyer_meeting(
    payload: MeetingRecordingCreate,
    db: Session = Depends(get_db),
):
    recording = MeetingRecording(
        source=payload.source,
        external_id=payload.external_id,
        title=payload.title,
        description=payload.description,
        participants=(
            [p.model_dump() for p in payload.participants]
            if payload.participants
            else None
        ),
        raw_transcript=payload.raw_transcript,
        transcript_json=payload.transcript_json,
        tags=payload.tags,
        related_case_id=payload.related_case_id,
        metadata_json=payload.metadata,
    )

    db.add(recording)
    db.flush()

    # If it's tied to a God Review Case, log an event there
    if payload.related_case_id:
        from app.god.models import GodReviewEvent

        event = GodReviewEvent(
            case_id=payload.related_case_id,
            actor="lawyer",
            event_type="meeting_ingested",
            message=payload.title or "Lawyer meeting ingested",
            payload={
                "recording_id": str(recording.id),
                "tags": payload.tags,
                "metadata": payload.metadata,
            },
        )
        db.add(event)

    db.commit()
    db.refresh(recording)
    return recording


@router.get("/recordings/{recording_id}", response_model=MeetingRecordingRead)
def get_recording(
    recording_id: UUID,
    db: Session = Depends(get_db),
):
    result = db.execute(
        select(MeetingRecording).where(MeetingRecording.id == recording_id)
    )
    recording = result.scalar_one_or_none()
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
    return recording
