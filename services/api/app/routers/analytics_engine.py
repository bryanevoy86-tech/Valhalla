"""
PACK AK: Analytics / Metrics Engine Router
Prefix: /analytics
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.analytics_engine import AnalyticsSnapshot
from app.services.analytics_engine import get_analytics_snapshot

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/snapshot", response_model=AnalyticsSnapshot)
def analytics_snapshot_endpoint(
    db: Session = Depends(get_db),
):
    """Get a comprehensive analytics snapshot of the empire."""
    data = get_analytics_snapshot(db)
    return AnalyticsSnapshot(**data)
