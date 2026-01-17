"""
PACK AN: Integrity Monitor Router
Prefix: /integrity
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.integrity_monitor import IntegrityReport
from app.services.integrity_monitor import generate_integrity_report

router = APIRouter(prefix="/integrity", tags=["Integrity"])


@router.get("/report", response_model=IntegrityReport)
def integrity_report_endpoint(
    db: Session = Depends(get_db),
):
    """Generate a comprehensive integrity report of the system."""
    return generate_integrity_report(db)
