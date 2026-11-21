"""Private owner memory with source attribution, scope, and append-only corrections."""
from typing import Literal
from uuid import UUID

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import exists, or_, select
from sqlalchemy.orm import Session, aliased

from app.models.owner_conversation import OwnerMemoryEntry, OwnerTurn


class MemoryIn(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    entry_id: UUID
    source_turn_id: UUID
    supersedes_id: UUID | None = None
    kind: Literal["PREFERENCE", "DECISION", "OBLIGATION", "ASSUMPTION", "SIMULATION"]
    visibility: Literal["CONVERSATION", "OWNER"] = "CONVERSATION"
    topic: str = Field(min_length=1, max_length=120)
    statement: str = Field(min_length=1, max_length=1500)
    state: Literal["RECORDED", "OPEN", "DONE", "RETRACTED"] = "RECORDED"


def memory_receipt(entry: OwnerMemoryEntry) -> dict:
    return {
        "entry_id": str(entry.id), "conversation_id": str(entry.conversation_id),
        "source_turn_id": str(entry.source_turn_id),
        "supersedes_id": str(entry.supersedes_id) if entry.supersedes_id else None,
        "kind": entry.kind, "visibility": entry.visibility, "topic": entry.topic,
        "statement": entry.statement, "state": entry.state, "created_at": entry.created_at.isoformat(),
        "evidence_class": entry.kind if entry.kind in {"ASSUMPTION", "SIMULATION"} else "OWNER_REPORTED",
        "verified_fact": False, "execution_authorized": False,
    }


def prepare_entry(db: Session, conversation_id: UUID, payload: MemoryIn) -> OwnerMemoryEntry:
    if payload.kind == "OBLIGATION":
        if payload.state not in {"OPEN", "DONE", "RETRACTED"}:
            raise HTTPException(422, "Obligations require an explicit open or closed state")
    elif payload.state not in {"RECORDED", "RETRACTED"}:
        raise HTTPException(422, "Only an obligation can be open or done")
    if payload.state in {"DONE", "RETRACTED"} and payload.supersedes_id is None:
        raise HTTPException(422, "Closing or retracting a record requires its prior entry")

    values = payload.model_dump(exclude={"entry_id"})
    existing = db.get(OwnerMemoryEntry, payload.entry_id)
    if existing is not None:
        if existing.conversation_id != conversation_id or any(getattr(existing, key) != v for key, v in values.items()):
            raise HTTPException(409, "Memory entry ID already exists")
        return existing

    source = db.get(OwnerTurn, payload.source_turn_id)
    if source is None or source.conversation_id != conversation_id:
        raise HTTPException(404, "Source turn not found in conversation")
    if payload.supersedes_id:
        prior = db.get(OwnerMemoryEntry, payload.supersedes_id, with_for_update=True)
        if prior is None or (prior.conversation_id != conversation_id and prior.visibility != "OWNER"):
            raise HTTPException(404, "Prior memory not found in scope")
        if (prior.kind, prior.visibility, prior.topic) != (payload.kind, payload.visibility, payload.topic):
            raise HTTPException(409, "A correction must retain topic, kind, and visibility")
        if db.scalar(select(OwnerMemoryEntry.id).where(OwnerMemoryEntry.supersedes_id == prior.id)) is not None:
            raise HTTPException(409, "Prior memory already has a correction")
    entry = OwnerMemoryEntry(id=payload.entry_id, conversation_id=conversation_id, **values)
    db.add(entry)
    return entry


def recall_entries(db: Session, conversation_id: UUID, limit: int = 15, *, open_only: bool = False) -> list[dict]:
    entry = OwnerMemoryEntry
    correction = aliased(entry)
    query = select(entry).where(
        or_(entry.conversation_id == conversation_id, entry.visibility == "OWNER"),
        ~exists(select(correction.id).where(correction.supersedes_id == entry.id)),
        entry.state != "RETRACTED",
    )
    if open_only:
        query = query.where(entry.kind == "OBLIGATION", entry.state == "OPEN")
    records = db.scalars(query.order_by(entry.created_at.desc(), entry.id.desc()).limit(limit)).all()
    return [memory_receipt(record) for record in records]
