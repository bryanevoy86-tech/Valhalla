"""PACK 86: Narrative Documentary Engine - Service"""

from sqlalchemy.orm import Session

from app.models.narrative_record import NarrativeEvent, NarrativeChapter
from app.schemas.narrative_record import NarrativeEventCreate, NarrativeChapterCreate


# Narrative event operations
def log_event(db: Session, event: NarrativeEventCreate) -> NarrativeEvent:
    db_event = NarrativeEvent(
        category=event.category,
        title=event.title,
        description=event.description,
        emotion_level=event.emotion_level
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


def list_events(db: Session, category: str | None = None) -> list[NarrativeEvent]:
    q = db.query(NarrativeEvent)
    if category:
        q = q.filter(NarrativeEvent.category == category)
    return q.order_by(NarrativeEvent.id.desc()).all()


def get_event(db: Session, event_id: int) -> NarrativeEvent | None:
    return db.query(NarrativeEvent).filter(NarrativeEvent.id == event_id).first()


def update_event(db: Session, event_id: int, event: NarrativeEventCreate) -> NarrativeEvent | None:
    db_event = get_event(db, event_id)
    if not db_event:
        return None
    db_event.category = event.category
    db_event.title = event.title
    db_event.description = event.description
    db_event.emotion_level = event.emotion_level
    db.commit()
    db.refresh(db_event)
    return db_event


def delete_event(db: Session, event_id: int) -> bool:
    db_event = get_event(db, event_id)
    if not db_event:
        return False
    db.delete(db_event)
    db.commit()
    return True


# Narrative chapter operations
def create_chapter(db: Session, chapter: NarrativeChapterCreate) -> NarrativeChapter:
    db_chapter = NarrativeChapter(
        title=chapter.title,
        chapter_payload=chapter.chapter_payload
    )
    db.add(db_chapter)
    db.commit()
    db.refresh(db_chapter)
    return db_chapter


def list_chapters(db: Session) -> list[NarrativeChapter]:
    return db.query(NarrativeChapter).order_by(NarrativeChapter.id.desc()).all()


def get_chapter(db: Session, chapter_id: int) -> NarrativeChapter | None:
    return db.query(NarrativeChapter).filter(NarrativeChapter.id == chapter_id).first()


def update_chapter(db: Session, chapter_id: int, chapter: NarrativeChapterCreate) -> NarrativeChapter | None:
    db_chapter = get_chapter(db, chapter_id)
    if not db_chapter:
        return None
    db_chapter.title = chapter.title
    db_chapter.chapter_payload = chapter.chapter_payload
    db.commit()
    db.refresh(db_chapter)
    return db_chapter


def delete_chapter(db: Session, chapter_id: int) -> bool:
    db_chapter = get_chapter(db, chapter_id)
    if not db_chapter:
        return False
    db.delete(db_chapter)
    db.commit()
    return True
