"""Story Admin Router"""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db

from . import schemas, service

router = APIRouter(prefix="/story", tags=["story_admin"])


@router.get("/settings", response_model=schemas.StorySettingsRead)
def read_settings(db: Session = Depends(get_db)):
    """Get story engine settings."""
    settings = service.get_settings(db)
    return settings


@router.patch("/settings", response_model=schemas.StorySettingsRead)
def patch_settings(
    payload: schemas.StorySettingsUpdate,
    db: Session = Depends(get_db),
):
    """Update story engine settings."""
    return service.update_settings(db, payload)


@router.get("/sessions", response_model=List[schemas.StorySessionRead])
def read_sessions(limit: int = 100, db: Session = Depends(get_db)):
    """List story sessions."""
    return service.list_sessions(db, limit=limit)


@router.get("/sessions/{session_id}", response_model=schemas.StorySessionRead)
def read_session(session_id: UUID, db: Session = Depends(get_db)):
    """Get a specific story session."""
    s = service.get_session(db, session_id)
    if not s:
        raise HTTPException(status_code=404, detail="Story session not found")
    return s
