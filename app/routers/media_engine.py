"""
PACK AC: Content / Media Engine Router
Prefix: /media
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.media_engine import (
    MediaChannelCreate,
    MediaChannelUpdate,
    MediaChannelOut,
    MediaContentCreate,
    MediaContentOut,
    MediaPublishCreate,
    MediaPublishUpdate,
    MediaPublishOut,
)
from app.services.media_engine import (
    create_channel,
    update_channel,
    list_channels,
    create_content,
    list_content,
    get_content,
    create_publish_entry,
    update_publish_entry,
    list_publish_for_content,
)

router = APIRouter(prefix="/media", tags=["Media"])


@router.post("/channels", response_model=MediaChannelOut)
def create_channel_endpoint(
    payload: MediaChannelCreate,
    db: Session = Depends(get_db),
):
    """Create a new media channel (YouTube, Blog, TikTok, etc.)."""
    return create_channel(db, payload)


@router.get("/channels", response_model=List[MediaChannelOut])
def list_channels_endpoint(
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
):
    """List media channels with optional active-only filtering."""
    return list_channels(db, active_only=active_only)


@router.patch("/channels/{channel_id}", response_model=MediaChannelOut)
def update_channel_endpoint(
    channel_id: int,
    payload: MediaChannelUpdate,
    db: Session = Depends(get_db),
):
    """Update a media channel."""
    obj = update_channel(db, channel_id, payload)
    if not obj:
        raise HTTPException(status_code=404, detail="Channel not found")
    return obj


@router.post("/content", response_model=MediaContentOut)
def create_content_endpoint(
    payload: MediaContentCreate,
    db: Session = Depends(get_db),
):
    """Create a new media content item."""
    return create_content(db, payload)


@router.get("/content", response_model=List[MediaContentOut])
def list_content_endpoint(
    content_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """List media content with optional filtering by type."""
    return list_content(db, content_type=content_type)


@router.get("/content/{content_id}", response_model=MediaContentOut)
def get_content_endpoint(
    content_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific media content item by ID."""
    obj = get_content(db, content_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Content not found")
    return obj


@router.post("/publish", response_model=MediaPublishOut)
def create_publish_endpoint(
    payload: MediaPublishCreate,
    db: Session = Depends(get_db),
):
    """Create a publish entry (link content to a channel)."""
    return create_publish_entry(db, payload)


@router.patch("/publish/{publish_id}", response_model=MediaPublishOut)
def update_publish_endpoint(
    publish_id: int,
    payload: MediaPublishUpdate,
    db: Session = Depends(get_db),
):
    """Update a publish entry (change status, add external ref)."""
    obj = update_publish_entry(db, publish_id, payload)
    if not obj:
        raise HTTPException(status_code=404, detail="Publish entry not found")
    return obj


@router.get("/publish/by-content/{content_id}", response_model=List[MediaPublishOut])
def list_publish_for_content_endpoint(
    content_id: int,
    db: Session = Depends(get_db),
):
    """List all publish entries for a specific content item."""
    return list_publish_for_content(db, content_id)
