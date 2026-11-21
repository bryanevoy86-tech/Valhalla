"""Owner-only conversational gateway. No model or external effects in this first lane."""
from datetime import datetime, timezone
import base64
import binascii
import hashlib
import re
from uuid import UUID
from typing import Literal
from fastapi import Depends, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, defer
from app.core.db import get_db
from app.models.owner_conversation import OwnerConversation, OwnerTurn, OwnerAttachment, OwnerAttachmentExtraction
from app.models.prime_specialist_schedule import PrimeSpecialistSchedule
from app.models.go_live_state import GoLiveState
from app.services.system_self_check import run_system_self_check
from app.services.owner_advisory_model import advisory_reply
from app.services.owner_attachment_extraction import extract_local, extraction_receipt, verified_attachment
from app.services.owner_attachment_review import ReviewIn, attachment_use_blocked, latest_review, latest_reviews, require_local_use, restore_hold_active, retention_expired, review_receipt, save_review
from app.services.prime_business_execution import require_owner_mandate_key
from app.services.owner_memory import MemoryIn, decision_context_recall, memory_receipt, prepare_entry, recall_entries
from app.services.owner_operating_brief import operating_evidence
from app.services.owner_specialist_context import prime_decision_context, specialist_context

MAX_BYTES = 5 * 1024 * 1024
MAX_BODY = 7 * 1024 * 1024

class ThreadIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    conversation_id: UUID
    title: str = Field(min_length=1, max_length=160)

class TurnIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    turn_id: UUID
    message: str = Field(min_length=1, max_length=8000)
    attachment_ids: list[UUID] = Field(default_factory=list, max_length=8)
    provider_data_class: Literal["PRIVATE", "SYNTHETIC"] = "PRIVATE"
    specialist_schedule_id: UUID | None = None
    prime_decision_id: UUID | None = None
    knowledge_domain: str | None = Field(default=None, min_length=2, max_length=80, pattern=r"^[A-Za-z0-9 .-]+$")
    knowledge_jurisdiction: str | None = Field(default=None, max_length=80, pattern=r"^[A-Z0-9-]+$")

class UploadIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    attachment_id: UUID
    filename: str = Field(min_length=1, max_length=180)
    media_type: Literal["application/pdf", "image/jpeg", "image/png", "text/plain", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"]
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    content_base64: str = Field(min_length=4, max_length=4*((MAX_BYTES+2)//3))

class DeleteAttachmentIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    reason: Literal["OWNER_REQUEST", "RETENTION_EXPIRED"]


def thread(db, cid):
    row = db.get(OwnerConversation, cid)
    if row is None:
        raise HTTPException(404, "Conversation not found")
    return row

def meta(row):
    return {"attachment_id": row.id, "conversation_id": row.conversation_id,
            "filename": row.filename, "media_type": row.media_type, "sha256": row.sha256,
            "size_bytes": row.size_bytes, "created_at": row.created_at,
            "state": "DELETED" if row.deleted_at else "QUARANTINED_UNREVIEWED",
            "deleted_at": row.deleted_at, "deletion_reason": row.deletion_reason,
            "analysis_complete": False}


def deleted_source(attachment):
    return {"attachment_id": str(attachment.id), "source_sha256": attachment.sha256, "state": "SOURCE_DELETED"}

def turn_meta(row, db):
    evidence = row.evidence
    if evidence.get("source") == "local_attachment_extraction":
        extracts = []
        for receipt in evidence.get("extractions", []):
            attachment = db.get(OwnerAttachment, UUID(receipt["attachment_id"]))
            if attachment is None or attachment.conversation_id != row.conversation_id or attachment.sha256 != receipt["source_sha256"]:
                extracts.append({"attachment_id": receipt["attachment_id"], "state": "SOURCE_UNAVAILABLE"})
            elif attachment.deleted_at is not None:
                extracts.append(deleted_source(attachment))
            elif attachment_use_blocked(db, attachment):
                extracts.append({"attachment_id": receipt["attachment_id"], "state": "RESTRICTED",
                                 "source_sha256": attachment.sha256})
            else:
                extracts.append(receipt)
        evidence = {**evidence, "extractions": extracts}
    return {"turn_id": row.id, "conversation_id": row.conversation_id, "message": row.message,
            "reply": row.reply, "attachment_ids": row.attachment_ids, "evidence": evidence,
            "created_at": row.created_at, "external_effects": 0, "execution_authorized": False,
            "response_mode": "MODEL_ADVISORY_ONLY" if row.evidence.get("model_connected") else "DETERMINISTIC_READ_ONLY"}

def thread_meta(row):
    return {"conversation_id": row.id, "title": row.title, "created_at": row.created_at}

def commit(db):
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Record already exists or reference is invalid") from None
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(503, "Owner conversation storage unavailable") from None

async def bounded_upload(request: Request):
    body = bytearray()
    async for chunk in request.stream():
        if len(body)+len(chunk)>MAX_BODY:
            raise HTTPException(413, "Upload exceeds 7 MiB request limit")
        body.extend(chunk)
    try:
        return UploadIn.model_validate_json(body)
    except ValidationError:
        raise HTTPException(422, "Invalid attachment request") from None

def decode_upload(payload):
    # Store opaque bytes only. Signature checks are not malware scanning.
    try:
        if not re.fullmatch(r"[^/\\\\\x00-\x1f\x7f]+", payload.filename) or payload.filename in {".", ".."}:
            raise ValueError("filename")
        data = base64.b64decode(payload.content_base64, validate=True)
        if not 0<len(data)<=MAX_BYTES or hashlib.sha256(data).hexdigest()!=payload.sha256:
            raise ValueError("digest")
        signatures = {"application/pdf": b"%PDF-", "image/jpeg": b"\xff\xd8\xff", "image/png": b"\x89PNG\r\n\x1a\n",
                      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": b"PK\x03\x04",
                      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": b"PK\x03\x04"}
        if payload.media_type in signatures and not data.startswith(signatures[payload.media_type]):
            raise ValueError("signature")
        if payload.media_type == "text/plain":
            data.decode("utf-8")
    except (ValueError, UnicodeError, binascii.Error):
        raise HTTPException(422, "Attachment filename, bytes, checksum or declared type invalid") from None
    return data

def answer(db, message, attachments, turn_id=None, provider_data_class="PRIVATE"):
    text = " ".join(message.casefold().strip().rstrip("?! .").split())
    # Exact allowlisted conversational queries, not substring-triggered actions.
    questions = {"status", "what's happening with valhalla today", "what is happening with valhalla today",
                 "is anything preventing us from operating", "is there anything that needs my attention",
                 "what have the gods been working on", "what is the system status", "briefing", "morning briefing"}
    if text not in questions:
        # Only the explicitly authorized text inference lane may contact a provider.
        # Attachments are never forwarded by this path.
        if turn_id is not None and not attachments:
            try:
                advisory = advisory_reply(db, turn_id, message, provider_data_class)
            except SQLAlchemyError:
                db.rollback()
                raise HTTPException(503, "Advisory context unavailable") from None
            if advisory is not None:
                return advisory
        return ("I've saved your message in our conversation. Natural-language reasoning is unavailable for this request; no action was taken. "
                "I can provide a persisted system briefing if you ask for status. "
                + ("Your attachments are stored; I have not analyzed them." if attachments else ""),
                {"source": "conversation_inbox", "model_connected": False})
    try:
        report = run_system_self_check(db, record_alerts=False)
        release = db.get(GoLiveState, 1)
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        schedules = db.scalar(select(func.count()).select_from(PrimeSpecialistSchedule).where(
            PrimeSpecialistSchedule.state=="active", PrimeSpecialistSchedule.expires_at>now))
        reports = db.scalar(select(func.count()).select_from(PrimeSpecialistSchedule).where(
            PrimeSpecialistSchedule.last_report_event_id.is_not(None)))
        operating = operating_evidence(db)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(503, "System briefing evidence unavailable") from None
    signals = report["anomaly_detection"]["signals"]
    reply = ("Here is the recorded system briefing. "
             f"Persisted live flag: {release.go_live_enabled if release is not None else 'unknown'}. "
             f"Emergency stop active: {report['fail_safe_state']['active']}. "
             f"Observed integrity signals: {len(signals)}. "
             f"Active advisory schedules: {schedules}; schedules referencing a report: {reports}. "
             "These are limited internal checks, not proof of live readiness or commercial results.")
    reply += f" Recent verified specialist receipts: {len(operating['latest_specialist_reports'])}."
    if operating["specialist_cadence_alerts"]:
        reply += f" Recent specialist reports covering missed schedule slots: {len(operating['specialist_cadence_alerts'])}."
    if operating["loki"]["available"]:
        reply += f" Loki reviews queued: {operating['loki']['queued_count']}. Recent unresolved or unverified reviews: {len(operating['loki']['latest_outstanding'])}."
    advisory = operating["latest_prime_advisory_alerts"]
    unverified = operating["invalid_prime_report_refs"]
    if advisory or unverified:
        reply += f" Active Prime advisories needing attention: {len(advisory)}. Unverified Prime receipts: {len(unverified)}."
    economic = operating["latest_economic_alerts"]
    if economic:
        reply += f" Recent specialist reports flagged economic restrictions in {len(economic)} operating scope(s)."
    intake = operating["foundry_intake_health"]
    if intake["available"]:
        pending = intake["counts_by_state"].get("QUEUED", 0)
        reply += f" Discovery intake has {pending} queued job(s). Scoped health evidence is attached."
    if operating["financials"]["available"]:
        reply += " Recorded unreconciled revenue entries are attached by currency."
    if signals:
        reply += " Attention: " + "; ".join(signals.values()) + "."
    if attachments:
        reply += " Attached files are stored but not analyzed."
    return reply, {"source": "persisted_integrity_and_specialist_schedules", "integrity": report,
                   "live_flag": release.go_live_enabled if release is not None else None,
                   "active_advisory_schedules": schedules, "schedules_with_report_reference": reports,
                   "operating_evidence": operating,
                   "model_connected": False}

def conversation_summaries(db: Session, limit: int):
    rows = db.scalars(select(OwnerConversation).order_by(OwnerConversation.created_at.desc(), OwnerConversation.id)
                      .limit(max(1, min(limit, 100)))).all()
    return [thread_meta(row) for row in rows]


def conversation_history(db: Session, conversation_id: UUID, limit: int):
    thread(db, conversation_id)
    rows = db.scalars(select(OwnerTurn).where(OwnerTurn.conversation_id == conversation_id)
                      .order_by(OwnerTurn.created_at.desc(), OwnerTurn.id.desc())
                      .limit(max(1, min(limit, 100)))).all()
    return [turn_meta(row, db) for row in reversed(rows)]


def create_conversation(payload: ThreadIn, db: Session):
    title = payload.title.strip()
    if not title:
        raise HTTPException(422, "Title cannot be blank")
    existing = db.get(OwnerConversation, payload.conversation_id)
    if existing:
        if existing.title != title:
            raise HTTPException(409, "Conversation ID already used")
        return thread_meta(existing)
    row = OwnerConversation(id=payload.conversation_id, title=title)
    db.add(row)
    commit(db)
    return thread_meta(row)


def submit_turn(conversation_id: UUID, payload: TurnIn, db: Session, *, local_only: bool = False):
    thread(db, conversation_id)
    if local_only and payload.provider_data_class != "PRIVATE":
        raise HTTPException(422, "WeWeb conversation accepts private local turns only")
    message = payload.message.strip()
    ids = [str(x) for x in payload.attachment_ids]
    if not message or len(set(ids)) != len(ids):
        raise HTTPException(422, "Blank message or duplicate attachment")
    if sum(reference is not None for reference in (
        payload.prime_decision_id, payload.specialist_schedule_id, payload.knowledge_domain,
    )) > 1 or (payload.knowledge_jurisdiction and not payload.knowledge_domain):
        raise HTTPException(422, "Specify one scoped evidence reference per turn")
    knowledge_scope = ({"domain": payload.knowledge_domain, "jurisdiction": payload.knowledge_jurisdiction}
                       if payload.knowledge_domain else None)
    existing = db.get(OwnerTurn, payload.turn_id)
    if existing:
        if (existing.conversation_id, existing.message, existing.attachment_ids)!=(conversation_id,message,ids):
            raise HTTPException(409, "Turn ID already used")
        if existing.evidence.get("requested_provider_class", "PRIVATE") != payload.provider_data_class:
            raise HTTPException(409, "Turn classification already recorded")
        if existing.evidence.get("requested_specialist_schedule_id") != (
            str(payload.specialist_schedule_id) if payload.specialist_schedule_id else None
        ):
            raise HTTPException(409, "Turn specialist reference already recorded")
        if existing.evidence.get("requested_prime_decision_id") != (
            str(payload.prime_decision_id) if payload.prime_decision_id else None
        ):
            raise HTTPException(409, "Turn Prime decision reference already recorded")
        if existing.evidence.get("requested_knowledge_scope") != knowledge_scope:
            raise HTTPException(409, "Turn knowledge scope already recorded")
        return turn_meta(existing, db)
    # Acquire consistently ordered locks before writing a turn that refers to raw bytes.
    attachments = {aid: verified_attachment(db, conversation_id, aid, lock=True)
                   for aid in sorted(payload.attachment_ids)}
    normalized = " ".join(message.casefold().rstrip("?! .").split())
    if payload.prime_decision_id:
        evidence = prime_decision_context(db, payload.prime_decision_id)
        evidence.update(source="persisted_prime_decision", model_connected=False)
        reply = (
            f"Recorded Prime recommendation: {evidence['heimdall_decision'] or 'none'}. "
            f"Loki reconsideration: {evidence['independent_loki']['reconsideration_status']}. "
            "This recommendation grants no execution authority."
        )
    elif payload.specialist_schedule_id:
        evidence = specialist_context(db, payload.specialist_schedule_id)
        evidence.update(source="persisted_specialist_receipt", model_connected=False)
        reply = (
            f"Specialist report {evidence['report_event_id']} is {evidence['status']}. "
            f"Recorded recommendation: {evidence['heimdall_decision'] or 'none'}. "
            "This report is advisory and grants no execution authority."
        )
    elif knowledge_scope:
        from app.routers.completion_registry import KnowledgeRetrieveIn, _retrieve_knowledge

        request = KnowledgeRetrieveIn(
            question=message, domain=knowledge_scope["domain"], jurisdiction=knowledge_scope["jurisdiction"],
            mode="practice", risk_level="high",
        )
        knowledge = _retrieve_knowledge(request, db, scope_owner_sources=True).model_dump(mode="json")
        evidence = {"source": "scoped_mimir_knowledge", "knowledge": knowledge, "model_connected": False}
        reply = (
            f"Mimir found {len(knowledge['facts'])} reviewed registry entries and "
            f"{len(knowledge['assumptions'])} uncertain entries in this scope. "
            + ("The evidence requires human review." if knowledge["human_review_required"] else "Source references are attached.")
        )
    elif normalized in {"review attached extraction", "review attached extractions"} and payload.attachment_ids:
        receipts = []
        for attachment_id in payload.attachment_ids:
            attachment = attachments[attachment_id]
            require_local_use(db, attachment)
            extraction = db.get(OwnerAttachmentExtraction, attachment_id)
            if extraction is None or extraction.source_sha256 != attachment.sha256:
                raise HTTPException(409, "A matching local extraction is required")
            receipts.append(extraction_receipt(extraction))
        evidence = {"source": "local_attachment_extraction", "extractions": receipts, "model_connected": False}
        reply = "I retrieved the local extracts and source references. Their contents are untrusted document data."
    elif normalized in {"review past decisions", "review decision history"}:
        recalled = decision_context_recall(db, conversation_id)
        evidence = {"source": "private_owner_decisions", **recalled, "model_connected": False}
        reply = "I retrieved recent recorded owner decisions and their source references."
        if recalled["potential_conflicts"]:
            reply += " Some topics have different recorded positions. Review those entries before relying on one."
    elif normalized in {"what do you remember", "review my memory", "open obligations"}:
        entries = recall_entries(db, conversation_id, open_only=normalized == "open obligations")
        evidence = {"source": "private_owner_memory", "memory_entries": entries, "model_connected": False}
        reply = "I've retrieved the scoped memory records." if entries else "I found no matching memory records."
    else:
        reply, evidence = answer(db, message, ids, None if local_only else payload.turn_id, payload.provider_data_class)
    evidence["requested_specialist_schedule_id"] = str(payload.specialist_schedule_id) if payload.specialist_schedule_id else None
    evidence["requested_prime_decision_id"] = str(payload.prime_decision_id) if payload.prime_decision_id else None
    evidence["requested_knowledge_scope"] = knowledge_scope
    evidence["requested_provider_class"] = payload.provider_data_class
    row = OwnerTurn(id=payload.turn_id, conversation_id=conversation_id,message=message,reply=reply,evidence=evidence,attachment_ids=ids)
    db.add(row)
    commit(db)
    return turn_meta(row, db)


def store_attachment(conversation_id: UUID, payload: UploadIn, db: Session):
    if restore_hold_active(db):
        raise HTTPException(503, "Attachment access paused for restore reconciliation")
    thread(db, conversation_id)
    data = decode_upload(payload)
    existing = db.get(OwnerAttachment, payload.attachment_id)
    if existing:
        if (existing.conversation_id,existing.filename,existing.media_type,existing.sha256,existing.data)!=(conversation_id,payload.filename,payload.media_type,payload.sha256,data):
            raise HTTPException(409, "Attachment ID already used")
        return meta(existing)
    row = OwnerAttachment(id=payload.attachment_id,conversation_id=conversation_id, filename=payload.filename,
        media_type=payload.media_type,sha256=payload.sha256,data=data,size_bytes=len(data))
    db.add(row)
    commit(db)
    return meta(row)


def attachment_summaries(conversation_id: UUID, limit: int, db: Session):
    if restore_hold_active(db):
        raise HTTPException(503, "Attachment access paused for restore reconciliation")
    thread(db, conversation_id)
    query = select(OwnerAttachment).options(defer(OwnerAttachment.data)).where(
        OwnerAttachment.conversation_id == conversation_id,
    ).order_by(OwnerAttachment.created_at.desc(), OwnerAttachment.id).limit(max(1, min(limit, 100)))
    attachments = db.scalars(query).all()
    reviews = latest_reviews(db, [row.id for row in attachments if row.deleted_at is None])
    summaries = []
    for row in attachments:
        summary = meta(row)
        review = reviews.get(row.id)
        if review is not None:
            state = review.disposition
            if review.source_sha256 != row.sha256:
                state = "REVIEW_UNVERIFIED"
            elif retention_expired(review):
                state = "RETENTION_EXPIRED"
            summary.update(state=state, retain_until=review.retain_until)
        summaries.append(summary)
    return summaries


def delete_attachment(conversation_id: UUID, attachment_id: UUID, payload: DeleteAttachmentIn, db: Session):
    attachment = db.get(OwnerAttachment, attachment_id, with_for_update=True)
    if attachment is None or attachment.conversation_id != conversation_id:
        raise HTTPException(404, "Attachment not found in conversation")
    if attachment.sha256 != payload.source_sha256:
        raise HTTPException(409, "Deletion digest does not match the attachment")
    if attachment.deleted_at is not None:
        if attachment.deletion_reason != payload.reason:
            raise HTTPException(409, "Deletion reason already recorded")
        return meta(attachment)
    if payload.reason == "RETENTION_EXPIRED":
        review = latest_review(db, attachment)
        if not retention_expired(review) or review.source_sha256 != attachment.sha256:
            raise HTTPException(409, "Matching attachment retention deadline has not expired")
    extraction = db.get(OwnerAttachmentExtraction, attachment_id)
    if extraction is not None:
        db.delete(extraction)
    source = deleted_source(attachment)
    turns = db.scalars(select(OwnerTurn).where(OwnerTurn.conversation_id == conversation_id)
                       .order_by(OwnerTurn.id).with_for_update().execution_options(yield_per=100))
    for turn in turns:
        extracts = turn.evidence.get("extractions")
        if extracts and str(attachment_id) in turn.attachment_ids:
            turn.evidence = {**turn.evidence, "extractions": [
                source if receipt.get("attachment_id") == source["attachment_id"] else receipt
                for receipt in extracts
            ]}
    attachment.data = None
    attachment.filename = "[deleted]"
    attachment.deleted_at = datetime.now(timezone.utc)
    attachment.deletion_reason = payload.reason
    commit(db)
    return meta(attachment)


def local_extraction(conversation_id: UUID, attachment_id: UUID, db: Session):
    attachment = verified_attachment(db, conversation_id, attachment_id, lock=True)
    require_local_use(db, attachment)
    existing = db.get(OwnerAttachmentExtraction, attachment_id)
    if existing is not None:
        if existing.source_sha256 != attachment.sha256:
            raise HTTPException(409, "Stored extraction does not match the attachment")
        return extraction_receipt(existing)
    row = OwnerAttachmentExtraction(
        attachment_id=attachment_id, source_sha256=attachment.sha256, result=extract_local(attachment),
    )
    db.add(row)
    commit(db)
    return extraction_receipt(row)


def install(router):
    @router.post("/conversations", status_code=201)
    def create_thread(payload: ThreadIn, db: Session = Depends(get_db)):
        return create_conversation(payload, db)

    @router.get("/conversations")
    def list_threads(limit: int = 20, db: Session = Depends(get_db)):
        return conversation_summaries(db, limit)

    @router.get("/conversations/{conversation_id}/turns")
    def history(conversation_id: UUID, limit: int = 50, db: Session = Depends(get_db)):
        return conversation_history(db, conversation_id, limit)

    @router.post("/conversations/{conversation_id}/turns", status_code=201)
    def send(conversation_id: UUID, payload: TurnIn, db: Session = Depends(get_db)):
        return submit_turn(conversation_id, payload, db)

    @router.post("/conversations/{conversation_id}/memory", status_code=201)
    def save_memory(conversation_id: UUID, payload: MemoryIn, db: Session = Depends(get_db)):
        thread(db, conversation_id)
        entry = prepare_entry(db, conversation_id, payload)
        commit(db)
        return memory_receipt(entry)

    @router.get("/conversations/{conversation_id}/memory")
    def list_memory(conversation_id: UUID, limit: int = 15, db: Session = Depends(get_db)):
        thread(db, conversation_id)
        return recall_entries(db, conversation_id, max(1, min(limit, 50)))

    @router.post("/conversations/{conversation_id}/attachments", status_code=201)
    def upload(conversation_id: UUID, payload: UploadIn = Depends(bounded_upload), db: Session = Depends(get_db)):
        return store_attachment(conversation_id, payload, db)

    @router.get("/conversations/{conversation_id}/attachments")
    def attachments(conversation_id: UUID, limit: int = 50, db: Session = Depends(get_db)):
        thread(db, conversation_id)
        return attachment_summaries(conversation_id, limit, db)

    @router.post("/conversations/{conversation_id}/attachments/{attachment_id}/review", status_code=201,
                 dependencies=[Depends(require_owner_mandate_key)])
    def record_review(conversation_id: UUID, attachment_id: UUID, payload: ReviewIn, db: Session = Depends(get_db)):
        attachment = verified_attachment(db, conversation_id, attachment_id, lock=True)
        review = save_review(db, attachment, payload)
        commit(db)
        return review_receipt(review)

    @router.delete("/conversations/{conversation_id}/attachments/{attachment_id}",
                   dependencies=[Depends(require_owner_mandate_key)])
    def dispose_attachment(conversation_id: UUID, attachment_id: UUID, payload: DeleteAttachmentIn,
                           db: Session = Depends(get_db)):
        return delete_attachment(conversation_id, attachment_id, payload, db)

    @router.get("/conversations/{conversation_id}/attachments/{attachment_id}/review")
    def read_review(conversation_id: UUID, attachment_id: UUID, db: Session = Depends(get_db)):
        attachment = verified_attachment(db, conversation_id, attachment_id)
        review = latest_review(db, attachment)
        return review_receipt(review) if review is not None else {"disposition": "UNREVIEWED"}

    @router.post("/conversations/{conversation_id}/attachments/{attachment_id}/extract")
    def extract_attachment(conversation_id: UUID, attachment_id: UUID, db: Session = Depends(get_db)):
        return local_extraction(conversation_id, attachment_id, db)

    @router.get("/conversations/{conversation_id}/attachments/{attachment_id}/download")
    def download(conversation_id: UUID, attachment_id: UUID, db: Session = Depends(get_db)):
        thread(db, conversation_id)
        row = verified_attachment(db, conversation_id, attachment_id, lock=True)
        disposition = latest_review(db, row)
        if retention_expired(disposition):
            raise HTTPException(409, "Owner attachment retention has expired")
        return Response(content=row.data, media_type="application/octet-stream",headers={
            "Content-Disposition": f'attachment; filename="{attachment_id}.bin"',
            "X-Content-Type-Options": "nosniff", "Cache-Control": "no-store", "X-Artifact-SHA256": row.sha256})
