"""PACK 67: Story Video Engine Router
API endpoints for video generation and status tracking.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional

from app.core.db import get_db
from app.services.story_video_service import queue_video, update_video_status
from app.schemas.story_video import StoryVideoOut

router = APIRouter(prefix="/story-video", tags=["Story Video Engine"])


@router.post("/", response_model=StoryVideoOut)
def request_video(source_module: str, script_payload: str, db: Session = Depends(get_db)):
    """Request a new story video generation."""
    return queue_video(db, source_module, script_payload)


@router.post("/{video_id}/status", response_model=StoryVideoOut)
def set_video_status(video_id: int, status: str, output_path: Optional[str] = None, db: Session = Depends(get_db)):
    """Update video generation status and optionally set output path."""
    return update_video_status(db, video_id, status, output_path)
