"""Apply one owner-authorized attachment deadline in a restartable transaction."""
from fastapi import HTTPException
from sqlalchemy import inspect, select
from sqlalchemy.orm import Session

from app.models.owner_conversation import OwnerAttachment, OwnerAttachmentReview
from app.services.owner_attachment_review import retention_day, restore_hold_active
from app.services.owner_conversation import DeleteAttachmentIn, delete_attachment
from app.services.prime_business_execution import _emergency_stop_active


def expire_due_attachment(db: Session) -> dict:
    if _emergency_stop_active(db) or restore_hold_active():
        return {"status": "blocked"}
    schema = inspect(db.connection())
    if not all(schema.has_table(table.__tablename__) for table in (OwnerAttachment, OwnerAttachmentReview)):
        raise HTTPException(503, "Attachment retention schema not ready")
    attachment, review = OwnerAttachment, OwnerAttachmentReview
    latest = (select(review.id).where(review.attachment_id == attachment.id)
              .order_by(review.created_at.desc(), review.id.desc()).limit(1).correlate(attachment).scalar_subquery())
    candidate = db.execute(select(attachment.id, attachment.conversation_id, attachment.sha256)
                           .join(review, review.id == latest).where(
                               attachment.deleted_at.is_(None), review.source_sha256 == attachment.sha256,
                               review.retain_until < retention_day(),
                           ).order_by(review.retain_until, attachment.id)
                           .with_for_update(of=attachment, skip_locked=True).limit(1)).one_or_none()
    if candidate is None:
        return {"status": "idle"}
    # The manual disposition service rechecks the current digest and latest deadline under this lock.
    delete_attachment(candidate.conversation_id, candidate.id, DeleteAttachmentIn(
        source_sha256=candidate.sha256, reason="RETENTION_EXPIRED",
    ), db)
    return {"status": "expired", "external_effects": 0}
