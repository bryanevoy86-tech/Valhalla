"""Journal exact private document requests and apply them under a separate server mandate."""
from datetime import date
import json
from typing import Literal
from uuid import UUID

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import inspect, select

from app.loki.evidence import artifact_digest
from app.models.completion_registry import LegacyOrchestrationEvent
from app.services.owner_attachment_extraction import verified_attachment
from app.services.owner_attachment_review import ReviewIn, latest_review, review_receipt, save_review
from app.services.owner_conversation import DeleteAttachmentIn, commit, delete_attachment


class DocumentRequestIn(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    request_id: UUID
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    operation: Literal["ACCEPT_LOCAL", "REJECT", "DISPOSE"]
    reason: str = Field(min_length=1, max_length=1400)
    retain_until: date | None = None

    @model_validator(mode="after")
    def check_retention(self):
        if self.operation != "ACCEPT_LOCAL" and self.retain_until is not None:
            raise ValueError("Set a deadline only for local-use approval")
        return self


class DocumentApplyIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


def load_event(db, key, kind, *, lock=False):
    if not inspect(db.connection()).has_table(LegacyOrchestrationEvent.__tablename__):
        raise HTTPException(503, "Document request journal unavailable")
    query = select(LegacyOrchestrationEvent).filter_by(event_id=key)
    row = db.scalar(query.with_for_update() if lock else query)
    if row is None:
        return None
    try:
        entry = json.loads(row.payload_json)
        if row.event_type != kind or row.legacy_instance_id is not None or entry["sha256"] != artifact_digest(
            kind, key, entry["body"],
        ):
            raise ValueError
        return entry
    except (ValueError, KeyError, TypeError):
        raise HTTPException(409, "Document journal integrity failure") from None


def append_event(db, key, kind, body):
    entry = {"body": body, "sha256": artifact_digest(kind, key, body)}
    db.add(LegacyOrchestrationEvent(event_id=key, event_type=kind, payload_json=json.dumps(entry),
                                   message="Private owner document request event"))
    return entry


REQUEST = "OWNER_DOCUMENT_REQUEST"
APPLIED = "OWNER_DOCUMENT_REQUEST_APPLIED"


def read_request(db, owner_id, request_id, *, lock=False):
    entry = load_event(db, f"OWNER-DOC-{request_id}", REQUEST, lock=lock)
    if entry is None or entry["body"].get("owner_id") != owner_id:
        raise HTTPException(404, "Owner document request not found")
    return entry


def document_request_status(db, owner_id, request_id):
    entry = read_request(db, owner_id, request_id)
    applied = load_event(db, f"OWNER-DOC-APPLIED-{request_id}", APPLIED)
    if applied and applied["body"].get("request_sha256") != entry["sha256"]:
        raise HTTPException(409, "Document receipt does not match the request")
    return {"request": entry["body"], "request_sha256": entry["sha256"],
            "status": "APPLIED" if applied else "PENDING_MANDATE",
            "receipt": applied["body"]["receipt"] if applied else None,
            "execution_authorized": False, "provider_forwarding_authorized": False}


def request_document_action(db, owner_id, conversation_id, attachment_id, payload):
    key = f"OWNER-DOC-{payload.request_id}"
    supplied = {"owner_id": owner_id, "conversation_id": str(conversation_id), "attachment_id": str(attachment_id),
                **payload.model_dump(mode="json")}
    def compare(existing):
        if any(existing["body"].get(field) != value for field, value in supplied.items()):
            raise HTTPException(409, "Document request ID already used")
        return document_request_status(db, owner_id, payload.request_id)

    existing = load_event(db, key, REQUEST)
    if existing:
        return compare(existing)
    attachment = verified_attachment(db, conversation_id, attachment_id, lock=True)
    if attachment.sha256 != payload.source_sha256:
        raise HTTPException(409, "Document digest changed")
    review = latest_review(db, attachment)
    append_event(db, key, REQUEST, {**supplied, "prior_review_id": str(review.id) if review else None})
    try:
        commit(db)
    except HTTPException as exc:
        existing = load_event(db, key, REQUEST) if exc.status_code == 409 else None
        if existing is None:
            raise
        return compare(existing)
    return document_request_status(db, owner_id, payload.request_id)


def apply_document_request(db, owner_id, request_id, expected_sha256):
    entry = read_request(db, owner_id, request_id, lock=True)
    if expected_sha256 != entry["sha256"]:
        raise HTTPException(409, "Approval digest does not match the document request")
    key = f"OWNER-DOC-APPLIED-{request_id}"
    if load_event(db, key, APPLIED):
        return document_request_status(db, owner_id, request_id)

    from app.services.prime_business_execution import _emergency_stop_active

    if _emergency_stop_active(db):
        raise HTTPException(503, "Document approval paused by emergency stop")
    source = entry["body"]
    cid, aid = UUID(source["conversation_id"]), UUID(source["attachment_id"])
    attachment = verified_attachment(db, cid, aid, lock=True)
    review = latest_review(db, attachment)
    if (attachment.sha256 != source["source_sha256"]
            or (str(review.id) if review else None) != source["prior_review_id"]):
        raise HTTPException(409, "Document or review changed after the request")
    if source["operation"] == "DISPOSE":
        receipt = delete_attachment(cid, aid, DeleteAttachmentIn(source_sha256=attachment.sha256,
                                    reason="OWNER_REQUEST"), db, persist=False)
    else:
        review = save_review(db, attachment, ReviewIn(review_id=request_id,
                             **{k: source[k] for k in ("source_sha256", "reason", "retain_until")},
                             disposition=source["operation"]))
        db.flush()
        receipt = review_receipt(review)
    from fastapi.encoders import jsonable_encoder

    append_event(db, key, APPLIED, {"request_sha256": expected_sha256, "receipt": jsonable_encoder(receipt)})
    commit(db)
    return document_request_status(db, owner_id, request_id)
