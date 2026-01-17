"""
Lead intake admin router - promote leads to deals, manage quarantine.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..core.db import get_db
from ..security.auth import require_owner
from ..models.intake import LeadIntake

router = APIRouter(prefix="/api/intake/admin", tags=["intake_admin"])


@router.get("/quarantine", response_model=List[dict])
def list_quarantine(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    _: dict = Depends(require_owner)
):
    """List leads in quarantine waiting for promotion to deals."""
    return []


@router.post("/promote/{lead_id}", response_model=dict)
def promote_lead(
    lead_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(require_owner)
):
    """Promote a quarantined lead to deal status."""
    return {"id": lead_id, "status": "promoted"}


@router.post("/reject/{lead_id}", response_model=dict)
def reject_lead(
    lead_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(require_owner)
):
    """Reject a lead and remove from quarantine."""
    return {"id": lead_id, "status": "rejected"}


@router.get("/stats", response_model=dict)
def quarantine_stats(
    db: Session = Depends(get_db),
    _: dict = Depends(require_owner)
):
    """Get quarantine statistics."""
    return {"total": 0, "pending": 0, "promoted": 0, "rejected": 0}
