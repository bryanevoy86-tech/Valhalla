from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.db import get_db
from app.sync.models import GodSyncRecord, SyncStatus
from app.sync.schemas import (
    GodSyncRecordCreate,
    GodSyncRecordRead,
)
from app.god.schemas import GodReviewCaseCreate


router = APIRouter(prefix="/god-sync", tags=["Heimdall ↔ Loki Sync Engine"])


def _compare(heimdall: dict, loki: dict) -> str | None:
    """Returns conflict summary string if any conflict found."""
    if not heimdall or not loki:
        return None

    conflicts = []
    for key in heimdall:
        if key in loki and heimdall[key] != loki[key]:
            conflicts.append(f"{key}: Heimdall={heimdall[key]} | Loki={loki[key]}")

    return "\n".join(conflicts) if conflicts else None


@router.post("", response_model=GodSyncRecordRead)
def sync_payloads(
    payload: GodSyncRecordCreate,
    db: Session = Depends(get_db)
):
    record = GodSyncRecord(
        subject_type=payload.subject_type,
        subject_reference=payload.subject_reference,
        heimdall_payload=payload.heimdall_payload,
        loki_payload=payload.loki_payload,
    )

    conflict = _compare(payload.heimdall_payload, payload.loki_payload)

    if conflict:
        record.sync_status = SyncStatus.CONFLICT
        record.conflict_summary = conflict

        # Import here to avoid circular dependency
        from app.god.models import GodReviewCase, GodReviewEvent, GodCaseStatus, GodCaseOutcome
        
        # Forward conflict into the review-case system
        forward_case = GodReviewCase(
            subject_type=payload.subject_type,
            subject_reference=payload.subject_reference,
            title=f"Conflict detected: {payload.subject_reference}",
            description=conflict,
            status=GodCaseStatus.OPEN,
            heimdall_summary="Heimdall's proposal",
            heimdall_payload=payload.heimdall_payload,
            final_outcome=GodCaseOutcome.UNKNOWN,
        )
        db.add(forward_case)
        db.flush()
        
        # Add initial event
        initial_event = GodReviewEvent(
            case_id=forward_case.id,
            actor="system",
            event_type="sync",
            message=f"Sync conflict detected: {conflict}",
            payload={"heimdall": payload.heimdall_payload, "loki": payload.loki_payload},
        )
        db.add(initial_event)
        
        record.forwarded_case_id = forward_case.id

    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/{record_id}", response_model=GodSyncRecordRead)
def get_sync_record(
    record_id: UUID,
    db: Session = Depends(get_db)
):
    result = db.execute(
        select(GodSyncRecord).where(GodSyncRecord.id == record_id)
    )
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(404, "Sync record not found")

    return record
