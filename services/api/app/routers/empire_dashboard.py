"""
PACK AF: Unified Empire Dashboard Router
Prefix: /dashboard
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.services.empire_dashboard import get_empire_dashboard

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/empire")
def get_empire_dashboard_endpoint(
    db: Session = Depends(get_db),
):
    """
    Returns a single JSON snapshot of the empire:
    - system status (version, backend complete)
    - holdings summary (count, total estimated value)
    - deal pipelines (wholesale total, active, dispo assignments)
    - audit & governance counts (open audits, decisions)
    - education & children hub stats (enrollments, hubs)
    
    This is a read-only aggregation endpoint for Heimdall and the dashboard UI.
    """
    return get_empire_dashboard(db)
