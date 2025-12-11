"""
PACK TI: Financial Stress Early Warning Router
Prefix: /finance/stress
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.financial_stress import (
    FinancialIndicatorCreate,
    FinancialIndicatorOut,
    FinancialStressEventCreate,
    FinancialStressEventOut,
)
from app.services.financial_stress import (
    create_indicator,
    list_indicators,
    record_stress_event,
    resolve_stress_event,
)

router = APIRouter(prefix="/finance/stress", tags=["Financial Stress"])


@router.post("/indicators", response_model=FinancialIndicatorOut)
def create_indicator_endpoint(
    payload: FinancialIndicatorCreate,
    db: Session = Depends(get_db),
):
    """Create a financial stress indicator (threshold/alert)."""
    return create_indicator(db, payload)


@router.get("/indicators", response_model=List[FinancialIndicatorOut])
def list_indicators_endpoint(
    active_only: bool = Query(False),
    db: Session = Depends(get_db),
):
    """List all financial stress indicators."""
    return list_indicators(db, active_only=active_only)


@router.post("/events", response_model=FinancialStressEventOut)
def record_event_endpoint(
    payload: FinancialStressEventCreate,
    db: Session = Depends(get_db),
):
    """Record a financial stress event (threshold trigger)."""
    event = record_stress_event(db, payload)
    if not event:
        raise HTTPException(status_code=404, detail="Indicator not found")
    return event


@router.post("/events/{event_id}/resolve", response_model=FinancialStressEventOut)
def resolve_event_endpoint(
    event_id: int,
    db: Session = Depends(get_db),
):
    """Resolve a financial stress event."""
    event = resolve_stress_event(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event
