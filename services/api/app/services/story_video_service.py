"""PACK 67: Story Video Engine Service
Service layer for story video operations.
"""

from typing import Optional
from sqlalchemy.orm import Session

from app.models.story_video import StoryVideo


def queue_video(db: Session, source_module: str, script_payload: str) -> StoryVideo:
    """Queue a new video generation request."""
    item = StoryVideo(
        source_module=source_module,
        script_payload=script_payload,
        status="queued"
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def update_video_status(db: Session, video_id: int, status: str, output_path: Optional[str] = None) -> StoryVideo:
    """Update video status and optionally set output path."""
    item = db.query(StoryVideo).filter(StoryVideo.id == video_id).first()
    if item:
        item.status = status
        if output_path:
            item.output_path = output_path
        db.commit()
        db.refresh(item)
    return item
