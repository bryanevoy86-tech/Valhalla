"""Append owner dispositions without treating uploaded claims as verified."""
from datetime import date, datetime, timedelta, timezone
from typing import Literal
from uuid import UUID

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import inspect, select
from sqlalchemy.orm import Session

from app.models.owner_conversation import OwnerAttachment, OwnerAttachmentReview


class ReviewIn(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    review_id: UUID
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    disposition: Literal["ACCEPT_LOCAL", "REJECT"]
    retain_until: date | None = None
    reason: str = Field(min_length=1, max_length=1400)


def latest_review(db: Session, attachment: OwnerAttachment):
    table = OwnerAttachmentReview
    if not inspect(db.connection()).has_table(table.__tablename__):
        return None
    return db.scalar(select(table).where(table.attachment_id == attachment.id)
                     .order_by(table.created_at.desc(), table.id.desc()).limit(1))


def retention_day():
    return datetime.now(timezone.utc).date()


def retention_expired(decision):
    return bool(decision and decision.retain_until and retention_day() > decision.retain_until)


def attachment_use_blocked(db: Session, attachment: OwnerAttachment) -> bool:
    decision = latest_review(db, attachment)
    return decision is not None and (
        decision.source_sha256 != attachment.sha256
        or decision.disposition == "REJECT"
        or retention_expired(decision)
    )


def require_local_use(db: Session, attachment: OwnerAttachment):
    if attachment_use_blocked(db, attachment):
        raise HTTPException(409, "Owner attachment disposition or retention deadline blocks local use")


def review_receipt(review: OwnerAttachmentReview):
    return {
        "review_id": review.id, "attachment_id": review.attachment_id, "source_sha256": review.source_sha256,
        "disposition": review.disposition, "reason": review.reason, "created_at": review.created_at,
        "retain_until": review.retain_until,
        "verified_fact": False, "execution_authorized": False, "provider_forwarding_authorized": False,
    }


def save_review(db: Session, attachment: OwnerAttachment, payload: ReviewIn):
    if not inspect(db.connection()).has_table(OwnerAttachmentReview.__tablename__):
        raise HTTPException(503, "Attachment review schema unavailable")
    if payload.source_sha256 != attachment.sha256:
        raise HTTPException(409, "Attachment digest differs from reviewed bytes")
    existing = db.get(OwnerAttachmentReview, payload.review_id)
    values = payload.model_dump(exclude={"review_id"})
    if existing:
        if existing.attachment_id != attachment.id or any(
            getattr(existing, field) != value for field, value in values.items()
            if field != "retain_until" or value is not None
        ):
            raise HTTPException(409, "Review ID already used")
        return existing
    prior = latest_review(db, attachment)
    if prior and prior.retain_until and payload.retain_until is None:
        values["retain_until"] = prior.retain_until
    if payload.retain_until is not None and payload.retain_until > retention_day() + timedelta(days=366):
        raise HTTPException(422, "Retention deadline must be within one year")
    review = OwnerAttachmentReview(id=payload.review_id, attachment_id=attachment.id, **values)
    db.add(review)
    return review
