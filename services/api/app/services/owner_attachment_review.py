"""Append owner dispositions without treating uploaded claims as verified."""
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
    reason: str = Field(min_length=1, max_length=1400)


def latest_review(db: Session, attachment: OwnerAttachment):
    table = OwnerAttachmentReview
    if not inspect(db.connection()).has_table(table.__tablename__):
        return None
    return db.scalar(select(table).where(table.attachment_id == attachment.id)
                     .order_by(table.created_at.desc(), table.id.desc()).limit(1))


def require_local_use(db: Session, attachment: OwnerAttachment):
    decision = latest_review(db, attachment)
    if decision is not None and (decision.source_sha256 != attachment.sha256 or decision.disposition == "REJECT"):
        raise HTTPException(409, "Owner attachment disposition blocks local use")


def review_receipt(review: OwnerAttachmentReview):
    return {
        "review_id": review.id, "attachment_id": review.attachment_id, "source_sha256": review.source_sha256,
        "disposition": review.disposition, "reason": review.reason, "created_at": review.created_at,
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
        if existing.attachment_id != attachment.id or any(getattr(existing, field) != value for field, value in values.items()):
            raise HTTPException(409, "Review ID already used")
        return existing
    review = OwnerAttachmentReview(id=payload.review_id, attachment_id=attachment.id, **values)
    db.add(review)
    return review
