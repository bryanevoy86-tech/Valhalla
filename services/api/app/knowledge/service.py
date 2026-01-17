from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from typing import List
from app.knowledge.models import KnowledgeDoc
from app.knowledge.schemas import KnowledgeCreate


def _expiry(ttl_hours: int | None):
    if not ttl_hours:
        return None
    return datetime.now(timezone.utc) + timedelta(hours=ttl_hours)


def ingest(db: Session, payload: KnowledgeCreate) -> KnowledgeDoc:
    doc = KnowledgeDoc(
        source=payload.source,
        title=payload.title,
        content=payload.content,
        tags=payload.tags,
        expires_at=_expiry(payload.ttl_hours),
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def list_fresh(db: Session, tag: str | None = None) -> List[KnowledgeDoc]:
    now = datetime.now(timezone.utc)
    q = db.query(KnowledgeDoc).filter(
        (KnowledgeDoc.expires_at.is_(None)) | (KnowledgeDoc.expires_at > now)
    )
    if tag:
        q = q.filter(KnowledgeDoc.tags.ilike(f"%{tag}%"))
    return q.order_by(KnowledgeDoc.id.desc()).limit(200).all()


def purge_expired(db: Session) -> int:
    now = datetime.now(timezone.utc)
    expired = db.query(KnowledgeDoc).filter(
        KnowledgeDoc.expires_at.is_not(None),
        KnowledgeDoc.expires_at <= now,
    ).all()
    count = len(expired)
    for d in expired:
        db.delete(d)
    db.commit()
    return count
