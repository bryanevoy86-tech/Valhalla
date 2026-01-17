"""
PACK CI8: Narrative / Chapter Engine Router
Prefix: /intelligence/narrative
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.narrative import (
    NarrativeChapterIn,
    NarrativeChapterOut,
    NarrativeChapterList,
    NarrativeEventIn,
    NarrativeEventOut,
    NarrativeEventList,
    ActiveChapterSet,
    ActiveChapterOut,
)
from app.services.narrative import (
    upsert_chapter,
    list_chapters,
    add_event,
    list_events_for_chapter,
    set_active_chapter,
    get_active_chapter,
)

router = APIRouter(prefix="/intelligence/narrative", tags=["Intelligence", "Narrative"])


@router.post("/chapters", response_model=NarrativeChapterOut)
def upsert_chapter_endpoint(
    payload: NarrativeChapterIn,
    db: Session = Depends(get_db),
):
    """Create or update a narrative chapter."""
    return upsert_chapter(db, payload)


@router.get("/chapters", response_model=NarrativeChapterList)
def list_chapters_endpoint(
    db: Session = Depends(get_db),
):
    """List all narrative chapters in order."""
    items = list_chapters(db)
    return NarrativeChapterList(total=len(items), items=items)


@router.post("/events", response_model=NarrativeEventOut)
def add_event_endpoint(
    payload: NarrativeEventIn,
    db: Session = Depends(get_db),
):
    """Add an event to a chapter."""
    evt = add_event(db, payload)
    return NarrativeEventOut.model_validate(evt)


@router.get("/chapters/{chapter_id}/events", response_model=NarrativeEventList)
def list_events_endpoint(
    chapter_id: int,
    limit: int = Query(500, ge=1, le=5000),
    db: Session = Depends(get_db),
):
    """List all events for a chapter."""
    items = list_events_for_chapter(db, chapter_id=chapter_id, limit=limit)
    return NarrativeEventList(
        total=len(items),
        items=[NarrativeEventOut.model_validate(i) for i in items],
    )


@router.post("/active", response_model=ActiveChapterOut)
def set_active_chapter_endpoint(
    payload: ActiveChapterSet,
    db: Session = Depends(get_db),
):
    """Set the active chapter."""
    active = set_active_chapter(db, payload)
    return ActiveChapterOut.model_validate(active)


@router.get("/active", response_model=ActiveChapterOut)
def get_active_chapter_endpoint(
    db: Session = Depends(get_db),
):
    """Get the currently active chapter."""
    active = get_active_chapter(db)
    if not active:
        raise RuntimeError("Active chapter not set. Create a chapter first.")
    return ActiveChapterOut.model_validate(active)
