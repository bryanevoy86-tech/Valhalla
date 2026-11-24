"""Append owner dispositions without treating uploaded claims as verified."""
from datetime import date, datetime, timedelta, timezone
from hashlib import sha256
from hmac import compare_digest
from pathlib import Path
import os
import re
from typing import Literal
from uuid import UUID

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import exists, func, inspect, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.owner_conversation import OwnerAttachment, OwnerAttachmentExtraction, OwnerAttachmentReview


class ReviewIn(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    review_id: UUID
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    disposition: Literal["ACCEPT_LOCAL", "REJECT"]
    retain_until: date | None = None
    reason: str = Field(min_length=1, max_length=1400)


class DispositionReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid")
    attachment_id: UUID
    conversation_id: UUID
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    reason: Literal["OWNER_REQUEST", "RETENTION_EXPIRED"]


class DispositionManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal[1]
    receipts: list[DispositionReceipt] = Field(max_length=1000)


def restore_hold_active(db: Session) -> bool:
    disabled = {"", "0", "false", "off"}
    def flag(name: str) -> bool:
        return os.getenv(name, "").strip().lower() not in disabled

    if flag("VALHALLA_OWNER_ATTACHMENT_RESTORE_HOLD"):
        return True
    path = os.getenv("VALHALLA_OWNER_ATTACHMENT_RESTORE_MANIFEST", "").strip()
    expected = os.getenv("VALHALLA_OWNER_ATTACHMENT_RESTORE_MANIFEST_SHA256", "").strip()
    required = flag("VALHALLA_OWNER_ATTACHMENT_RESTORE_REQUIRED")
    if not (required or path or expected):
        return False
    if not path or not re.fullmatch(r"[a-f0-9]{64}", expected):
        return True
    try:
        with Path(path).open("rb") as source:
            raw = source.read(1_000_001)
        if len(raw) > 1_000_000 or not compare_digest(sha256(raw).hexdigest(), expected):
            return True
        manifest = DispositionManifest.model_validate_json(raw)
        indexed = {receipt.attachment_id: receipt for receipt in manifest.receipts}
        if len(indexed) != len(manifest.receipts):
            return True
        if not indexed:
            return False
        attachment, extraction = OwnerAttachment, OwnerAttachmentExtraction
        # A failed readiness probe must leave the caller's transaction usable for redacted reads.
        with db.begin_nested():
            rows = db.execute(select(attachment.id, attachment.conversation_id, attachment.sha256,
                                     attachment.deletion_reason).where(
                attachment.id.in_(indexed), attachment.deleted_at.is_not(None), attachment.data.is_(None),
                ~exists(select(extraction.attachment_id).where(extraction.attachment_id == attachment.id)),
            )).all()
        return len(rows) != len(indexed) or any(
            (row.conversation_id, row.sha256) != (indexed[row.id].conversation_id, indexed[row.id].source_sha256)
            or (row.deletion_reason != indexed[row.id].reason
                and not (indexed[row.id].reason == "RETENTION_EXPIRED" and row.deletion_reason == "OWNER_REQUEST"))
            for row in rows
        )
    except (OSError, ValueError, SQLAlchemyError):
        return True


def latest_review(db: Session, attachment: OwnerAttachment):
    table = OwnerAttachmentReview
    if not inspect(db.connection()).has_table(table.__tablename__):
        return None
    return db.scalar(select(table).where(table.attachment_id == attachment.id)
                     .order_by(table.created_at.desc(), table.id.desc()).limit(1))


def latest_reviews(db: Session, attachment_ids: list[UUID]) -> dict[UUID, OwnerAttachmentReview]:
    table = OwnerAttachmentReview
    if not attachment_ids or not inspect(db.connection()).has_table(table.__tablename__):
        return {}
    ranked = select(
        table.id, func.row_number().over(
            partition_by=table.attachment_id, order_by=(table.created_at.desc(), table.id.desc()),
        ).label("position"),
    ).where(table.attachment_id.in_(attachment_ids)).subquery()
    rows = db.scalars(select(table).join(ranked, ranked.c.id == table.id).where(ranked.c.position == 1))
    return {row.attachment_id: row for row in rows}


def retention_day():
    return datetime.now(timezone.utc).date()


def retention_expired(decision):
    return bool(decision and decision.retain_until and retention_day() > decision.retain_until)


def attachment_use_blocked(db: Session, attachment: OwnerAttachment) -> bool:
    if restore_hold_active(db):
        return True
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
