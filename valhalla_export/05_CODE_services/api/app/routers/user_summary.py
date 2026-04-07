"""
PACK AT: User-Facing Summary Snapshot Router
Prefix: /summaries
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.user_summary import UserSummaryCreate, UserSummaryOut
from app.services.user_summary import create_summary, list_summaries

router = APIRouter(prefix="/summaries", tags=["UserSummaries"])


@router.post("/", response_model=UserSummaryOut)
def create_summary_endpoint(
    payload: UserSummaryCreate,
    db: Session = Depends(get_db),
):
    """Create a new user summary."""
    return create_summary(db, payload)


@router.get("/", response_model=List[UserSummaryOut])
def list_summaries_endpoint(
    summary_type: Optional[str] = Query(None),
    audience: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """List summaries with optional filters."""
    return list_summaries(db, summary_type=summary_type, audience=audience, limit=limit)
