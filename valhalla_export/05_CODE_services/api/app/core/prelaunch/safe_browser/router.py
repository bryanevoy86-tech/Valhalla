"""Safe Browser Router - Kids Safe Browser Proxy"""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db

from . import schemas, service

router = APIRouter(prefix="/browser/kids", tags=["kids_browser"])


@router.post("/search", response_model=schemas.KidSearchResponse)
def kid_search(payload: schemas.KidSearchRequest, db: Session = Depends(get_db)):
    """Search for kid-safe content."""
    return service.run_kid_safe_search(db, payload)


@router.post("/navigate", response_model=schemas.PageContent)
def kid_navigate(payload: schemas.KidNavigateRequest, db: Session = Depends(get_db)):
    """Navigate to a kid-safe page."""
    return service.navigate_to_page(db, payload)


@router.get("/history", response_model=List[schemas.KidHistoryItem])
def kid_history(child_id: UUID, db: Session = Depends(get_db)):
    """Get browser history for a child."""
    items = service.list_history_for_child(db, child_id)
    return items
