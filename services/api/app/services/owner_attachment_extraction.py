"""Schedule local extraction of checksummed private attachments."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.owner_conversation import OwnerAttachment, OwnerAttachmentExtraction
from app.services.owner_attachment_review import restore_hold_active


def verified_attachment(db: Session, conversation_id, attachment_id, *, lock=False) -> OwnerAttachment:
    if restore_hold_active():
        raise HTTPException(503, "Attachment access paused for restore reconciliation")
    row = db.get(OwnerAttachment, attachment_id, with_for_update=lock)
    if row is None or row.conversation_id != conversation_id:
        raise HTTPException(404, "Attachment not found in conversation")
    if row.deleted_at is not None:
        raise HTTPException(410, "Attachment content was deleted")
    if len(row.data) != row.size_bytes or hashlib.sha256(row.data).hexdigest() != row.sha256:
        raise HTTPException(409, "Stored attachment integrity check failed")
    return row


def extraction_receipt(row):
    return {
        "attachment_id": str(row.attachment_id), "source_sha256": row.source_sha256,
        "created_at": row.created_at.isoformat(), "evidence_class": "UNTRUSTED_ATTACHMENT",
        "extractor_version": 2 if "ocr_status" in row.result else 1, "execution_authorized": False, "sent_to_provider": False, **row.result,
    }


def extract_local(attachment):
    parser = Path(__file__).with_name("attachment_parser.py")
    try:
        result = subprocess.run(
            [sys.executable, "-I", str(parser), attachment.media_type],
            input=attachment.data, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            env={}, timeout=8, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        raise HTTPException(503, "Local attachment extractor unavailable") from None
    if result.returncode != 0 or not 0 < len(result.stdout) <= 300_000:
        raise HTTPException(422, "Attachment could not be safely extracted")
    try:
        return json.loads(result.stdout)
    except ValueError:
        raise HTTPException(503, "Local attachment extraction receipt invalid") from None
