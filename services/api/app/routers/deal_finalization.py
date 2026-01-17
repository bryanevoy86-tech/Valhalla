# services/api/app/routers/deal_finalization.py

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Dict

from app.core.db import get_db
from app.schemas.deal_finalization import DealFinalizationStatus
from app.services.deal_finalization import (
    check_deal_ready_for_finalization,
    finalize_deal,
    get_finalization_requirements,
)

router = APIRouter(
    prefix="/deals/finalization",
    tags=["Deals", "Finalization"]
)


@router.get("/requirements")
def get_requirements_endpoint() -> Dict[str, str]:
    """
    Get the current finalization requirements configuration.
    Shows what status is needed for contracts, documents, and tasks.
    """
    return get_finalization_requirements()


@router.get("/status/{deal_id}", response_model=DealFinalizationStatus)
def get_finalization_status(deal_id: int, db: Session = Depends(get_db)):
    """
    Check if a deal is ready for finalization.
    Returns checklist breakdown of all requirements.
    """
    status = check_deal_ready_for_finalization(db, deal_id)
    status["finalized"] = None  # Just checking status, not finalizing
    return status


@router.post("/{deal_id}", response_model=DealFinalizationStatus)
def finalize_deal_endpoint(deal_id: int, db: Session = Depends(get_db)):
    """
    Finalize a deal if all requirements are met:
    - At least one signed contract
    - All document routes acknowledged
    - All professional tasks done
    
    If not ready, returns checklist with finalized=False.
    """
    status = finalize_deal(db, deal_id)
    return status
