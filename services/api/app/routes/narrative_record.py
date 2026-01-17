"""PACK 86: Narrative Documentary Engine - Router"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.narrative_record import NarrativeEventOut, NarrativeEventCreate, NarrativeChapterOut, NarrativeChapterCreate
from app.services.narrative_record_service import (
    log_event, list_events, get_event, update_event, delete_event,
    create_chapter, list_chapters, get_chapter, update_chapter, delete_chapter
)

router = APIRouter(prefix="/narrative", tags=["narrative_record"])


# Narrative event endpoints
@router.post("/event", response_model=NarrativeEventOut)
def post_event(event: NarrativeEventCreate, db: Session = Depends(get_db)):
    return log_event(db, event)


@router.get("/events", response_model=list[NarrativeEventOut])
def get_events_endpoint(category: str | None = None, db: Session = Depends(get_db)):
    return list_events(db, category)


@router.get("/event/{event_id}", response_model=NarrativeEventOut)
def get_event_endpoint(event_id: int, db: Session = Depends(get_db)):
    return get_event(db, event_id)


@router.put("/event/{event_id}", response_model=NarrativeEventOut)
def put_event(event_id: int, event: NarrativeEventCreate, db: Session = Depends(get_db)):
    return update_event(db, event_id, event)


@router.delete("/event/{event_id}")
def delete_event_endpoint(event_id: int, db: Session = Depends(get_db)):
    return delete_event(db, event_id)


# Narrative chapter endpoints
@router.post("/chapter", response_model=NarrativeChapterOut)
def post_chapter(chapter: NarrativeChapterCreate, db: Session = Depends(get_db)):
    return create_chapter(db, chapter)


@router.get("/chapters", response_model=list[NarrativeChapterOut])
def get_chapters_endpoint(db: Session = Depends(get_db)):
    return list_chapters(db)


@router.get("/chapter/{chapter_id}", response_model=NarrativeChapterOut)
def get_chapter_endpoint(chapter_id: int, db: Session = Depends(get_db)):
    return get_chapter(db, chapter_id)


@router.put("/chapter/{chapter_id}", response_model=NarrativeChapterOut)
def put_chapter(chapter_id: int, chapter: NarrativeChapterCreate, db: Session = Depends(get_db)):
    return update_chapter(db, chapter_id, chapter)


@router.delete("/chapter/{chapter_id}")
def delete_chapter_endpoint(chapter_id: int, db: Session = Depends(get_db)):
    return delete_chapter(db, chapter_id)
