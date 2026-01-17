"""
PACK CI8: Narrative / Chapter Engine Service
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.narrative import NarrativeChapter, NarrativeEvent, ActiveChapter
from app.schemas.narrative import NarrativeChapterIn, NarrativeEventIn, ActiveChapterSet


def upsert_chapter(
    db: Session,
    payload: NarrativeChapterIn,
) -> NarrativeChapter:
    """Create or update a narrative chapter by slug."""
    chapter = (
        db.query(NarrativeChapter)
        .filter(NarrativeChapter.slug == payload.slug)
        .first()
    )
    if not chapter:
        chapter = NarrativeChapter(**payload.model_dump())
        db.add(chapter)
    else:
        for field, value in payload.model_dump().items():
            setattr(chapter, field, value)

    db.commit()
    db.refresh(chapter)
    return chapter


def list_chapters(db: Session) -> List[NarrativeChapter]:
    """List all narrative chapters in order."""
    return (
        db.query(NarrativeChapter)
        .order_by(NarrativeChapter.phase_order.asc())
        .all()
    )


def add_event(
    db: Session,
    payload: NarrativeEventIn,
) -> NarrativeEvent:
    """Add an event to a chapter."""
    occurred_at = payload.occurred_at or datetime.utcnow()
    evt = NarrativeEvent(
        chapter_id=payload.chapter_id,
        title=payload.title,
        description=payload.description,
        tags=payload.tags,
        occurred_at=occurred_at,
        created_at=datetime.utcnow(),
    )
    db.add(evt)
    db.commit()
    db.refresh(evt)
    return evt


def list_events_for_chapter(
    db: Session,
    chapter_id: int,
    limit: int = 500,
) -> List[NarrativeEvent]:
    """List all events for a chapter."""
    return (
        db.query(NarrativeEvent)
        .filter(NarrativeEvent.chapter_id == chapter_id)
        .order_by(NarrativeEvent.occurred_at.desc())
        .limit(limit)
        .all()
    )


def set_active_chapter(
    db: Session,
    payload: ActiveChapterSet,
) -> ActiveChapter:
    """Set the current active chapter."""
    active = db.query(ActiveChapter).filter(ActiveChapter.id == 1).first()
    if not active:
        active = ActiveChapter(
            id=1,
            chapter_id=payload.chapter_id,
            reason=payload.reason,
        )
        db.add(active)
    else:
        active.chapter_id = payload.chapter_id
        active.reason = payload.reason
        active.changed_at = datetime.utcnow()

    db.commit()
    db.refresh(active)
    return active


def get_active_chapter(
    db: Session,
) -> Optional[ActiveChapter]:
    """Get the current active chapter."""
    return db.query(ActiveChapter).filter(ActiveChapter.id == 1).first()
