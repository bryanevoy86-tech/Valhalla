"""P-JOURNAL-1: Journal router."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from . import store

router = APIRouter(prefix="/core/journal", tags=["journal"])

class JournalRequest(BaseModel):
    text: str
    tags: list[str] | None = None

class JournalResponse(BaseModel):
    id: str
    text: str
    tags: list[str]
    created_at: str

@router.post("")
def add_entry(req: JournalRequest) -> JournalResponse:
    """Add a journal entry (brain dump)."""
    item = store.add(req.text, req.tags)
    return JournalResponse(**item)

@router.get("")
def list_entries(limit: int = 50) -> list[JournalResponse]:
    """List recent journal entries."""
    items = store.list_items(limit)
    return [JournalResponse(**item) for item in items]

@router.get("/search")
def search_entries(q: str) -> list[JournalResponse]:
    """Search journal entries by text."""
    items = store.search(q)
    return [JournalResponse(**item) for item in items]
