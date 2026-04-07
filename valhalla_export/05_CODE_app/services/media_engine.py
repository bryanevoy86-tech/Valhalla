"""
PACK AC: Content / Media Engine Service
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.media_engine import MediaChannel, MediaContent, MediaPublishLog
from app.schemas.media_engine import (
    MediaChannelCreate,
    MediaChannelUpdate,
    MediaContentCreate,
    MediaPublishCreate,
    MediaPublishUpdate,
)


# Channels

def create_channel(db: Session, payload: MediaChannelCreate) -> MediaChannel:
    obj = MediaChannel(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_channel(
    db: Session,
    channel_id: int,
    payload: MediaChannelUpdate,
) -> Optional[MediaChannel]:
    obj = db.query(MediaChannel).filter(MediaChannel.id == channel_id).first()
    if not obj:
        return None

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(obj, field, value)

    db.commit()
    db.refresh(obj)
    return obj


def list_channels(db: Session, active_only: bool = True) -> List[MediaChannel]:
    q = db.query(MediaChannel)
    if active_only:
        q = q.filter(MediaChannel.is_active.is_(True))
    return q.order_by(MediaChannel.created_at.desc()).all()


# Content

def create_content(db: Session, payload: MediaContentCreate) -> MediaContent:
    obj = MediaContent(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_content(db: Session, content_type: Optional[str] = None) -> List[MediaContent]:
    q = db.query(MediaContent)
    if content_type:
        q = q.filter(MediaContent.content_type == content_type)
    return q.order_by(MediaContent.created_at.desc()).all()


def get_content(db: Session, content_id: int) -> Optional[MediaContent]:
    return db.query(MediaContent).filter(MediaContent.id == content_id).first()


# Publish

def create_publish_entry(
    db: Session,
    payload: MediaPublishCreate,
) -> MediaPublishLog:
    obj = MediaPublishLog(**payload.model_dump())
    # if marking as published immediately
    if obj.status == "published" and not obj.published_at:
        obj.published_at = datetime.utcnow()
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_publish_entry(
    db: Session,
    publish_id: int,
    payload: MediaPublishUpdate,
) -> Optional[MediaPublishLog]:
    obj = db.query(MediaPublishLog).filter(MediaPublishLog.id == publish_id).first()
    if not obj:
        return None

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(obj, field, value)

    if obj.status == "published" and obj.published_at is None:
        obj.published_at = datetime.utcnow()

    db.commit()
    db.refresh(obj)
    return obj


def list_publish_for_content(
    db: Session,
    content_id: int,
) -> List[MediaPublishLog]:
    return (
        db.query(MediaPublishLog)
        .filter(MediaPublishLog.content_id == content_id)
        .order_by(MediaPublishLog.created_at.desc())
        .all()
    )
