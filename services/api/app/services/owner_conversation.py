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
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.models.owner_conversation import OwnerConversation, OwnerTurn, OwnerAttachment
from app.models.prime_specialist_schedule import PrimeSpecialistSchedule
from app.models.go_live_state import GoLiveState
from app.services.system_self_check import run_system_self_check
from app.services.owner_advisory_model import advisory_reply
from app.services.owner_memory import MemoryIn, memory_receipt, prepare_entry, recall_entries
from app.services.owner_specialist_context import specialist_context

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

class UploadIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    attachment_id: UUID
    filename: str = Field(min_length=1, max_length=180)
    media_type: Literal["application/pdf", "image/jpeg", "image/png", "text/plain", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"]
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    content_base64: str = Field(min_length=4, max_length=4*((MAX_BYTES+2)//3))

def thread(db, cid):
    row = db.get(OwnerConversation, cid)
    if row is None:
        raise HTTPException(404, "Conversation not found")
    return row

def meta(row):
    return {"attachment_id": row.id, "conversation_id": row.conversation_id,
            "filename": row.filename, "media_type": row.media_type, "sha256": row.sha256,
            "size_bytes": row.size_bytes, "created_at": row.created_at,
            "state": "QUARANTINED_UNREVIEWED", "analysis_complete": False}

def turn_meta(row):
    return {"turn_id": row.id, "conversation_id": row.conversation_id, "message": row.message,
            "reply": row.reply, "attachment_ids": row.attachment_ids, "evidence": row.evidence,
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
    if signals:
        reply += " Attention: " + "; ".join(signals.values()) + "."
    if attachments:
        reply += " Attached files are stored but not analyzed."
    return reply, {"source": "persisted_integrity_and_specialist_schedules", "integrity": report,
                   "live_flag": release.go_live_enabled if release is not None else None,
                   "active_advisory_schedules": schedules, "schedules_with_report_reference": reports,
                   "model_connected": False}

def install(router):
    @router.post("/conversations", status_code=201)
    def create_thread(payload: ThreadIn, db: Session = Depends(get_db)):
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

    @router.get("/conversations")
    def list_threads(limit: int = 20, db: Session = Depends(get_db)):
        rows = db.scalars(select(OwnerConversation).order_by(OwnerConversation.created_at.desc(), OwnerConversation.id).limit(max(1,min(limit,100)))).all()
        return [thread_meta(row) for row in rows]

    @router.get("/conversations/{conversation_id}/turns")
    def history(conversation_id: UUID, limit: int = 50, db: Session = Depends(get_db)):
        thread(db, conversation_id)
        rows = db.scalars(select(OwnerTurn).where(OwnerTurn.conversation_id==conversation_id).order_by(OwnerTurn.created_at.desc(),OwnerTurn.id.desc()).limit(max(1,min(limit,100)))).all()
        return [turn_meta(row) for row in reversed(rows)]

    @router.post("/conversations/{conversation_id}/turns", status_code=201)
    def send(conversation_id: UUID, payload: TurnIn, db: Session = Depends(get_db)):
        thread(db, conversation_id)
        message = payload.message.strip()
        ids = [str(x) for x in payload.attachment_ids]
        if not message or len(set(ids)) != len(ids):
            raise HTTPException(422, "Blank message or duplicate attachment")
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
            return turn_meta(existing)
        for aid in payload.attachment_ids:
            row = db.get(OwnerAttachment, aid)
            if row is None or row.conversation_id != conversation_id:
                raise HTTPException(404, "Attachment not found in conversation")
        normalized = " ".join(message.casefold().rstrip("?! .").split())
        if payload.specialist_schedule_id:
            evidence = specialist_context(db, payload.specialist_schedule_id)
            evidence.update(source="persisted_specialist_receipt", model_connected=False)
            reply = (
                f"Specialist report {evidence['report_event_id']} is {evidence['status']}. "
                f"Recorded recommendation: {evidence['heimdall_decision'] or 'none'}. "
                "This report is advisory and grants no execution authority."
            )
        elif normalized in {"what do you remember", "review my memory", "open obligations"}:
            entries = recall_entries(db, conversation_id, open_only=normalized == "open obligations")
            evidence = {"source": "private_owner_memory", "memory_entries": entries, "model_connected": False}
            reply = "I've retrieved the scoped memory records." if entries else "I found no matching memory records."
        else:
            reply, evidence = answer(db, message, ids, payload.turn_id, payload.provider_data_class)
        evidence["requested_specialist_schedule_id"] = str(payload.specialist_schedule_id) if payload.specialist_schedule_id else None
        evidence["requested_provider_class"] = payload.provider_data_class
        row = OwnerTurn(id=payload.turn_id, conversation_id=conversation_id,message=message,reply=reply,evidence=evidence,attachment_ids=ids)
        db.add(row)
        commit(db)
        return turn_meta(row)

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

    @router.get("/conversations/{conversation_id}/attachments")
    def attachments(conversation_id: UUID, limit: int = 50, db: Session = Depends(get_db)):
        thread(db, conversation_id)
        # Avoid loading file bytes for a metadata-only response.
        from sqlalchemy.orm import defer
        rows = db.scalars(select(OwnerAttachment).options(defer(OwnerAttachment.data)).where(
            OwnerAttachment.conversation_id==conversation_id).order_by(OwnerAttachment.created_at.desc(),OwnerAttachment.id).limit(max(1,min(limit,100)))).all()
        return [meta(row) for row in rows]

    @router.get("/conversations/{conversation_id}/attachments/{attachment_id}/download")
    def download(conversation_id: UUID, attachment_id: UUID, db: Session = Depends(get_db)):
        thread(db, conversation_id)
        row = db.get(OwnerAttachment, attachment_id)
        if row is None or row.conversation_id!=conversation_id:
            raise HTTPException(404, "Attachment not found in conversation")
        if len(row.data)!=row.size_bytes or hashlib.sha256(row.data).hexdigest()!=row.sha256:
            raise HTTPException(409, "Stored attachment integrity check failed")
        return Response(content=row.data, media_type="application/octet-stream",headers={
            "Content-Disposition": f'attachment; filename="{attachment_id}.bin"',
            "X-Content-Type-Options": "nosniff", "Cache-Control": "no-store", "X-Artifact-SHA256": row.sha256})
