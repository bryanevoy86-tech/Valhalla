"""
PACK Z: Global Holdings Engine Router
Prefix: /holdings
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.holdings import (
    HoldingCreate,
    HoldingUpdate,
    HoldingOut,
    HoldingsSummary,
)
from app.services.holdings_engine import (
    create_holding,
    update_holding,
    get_holding,
    list_holdings,
    summarize_holdings,
)

router = APIRouter(prefix="/holdings", tags=["Holdings"])


@router.post("/", response_model=HoldingOut)
def create_holding_endpoint(
    payload: HoldingCreate,
    db: Session = Depends(get_db),
):
    """Create a new holding."""
    return create_holding(db, payload)


@router.get("/", response_model=List[HoldingOut])
def list_holdings_endpoint(
    asset_type: Optional[str] = Query(None),
    jurisdiction: Optional[str] = Query(None),
    only_active: bool = Query(True),
    db: Session = Depends(get_db),
):
    """List holdings, optionally filtered by asset type or jurisdiction."""
    return list_holdings(
        db,
        asset_type=asset_type,
        jurisdiction=jurisdiction,
        only_active=only_active,
    )


@router.get("/{holding_id}", response_model=HoldingOut)
def get_holding_endpoint(
    holding_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific holding."""
    h = get_holding(db, holding_id)
    if not h:
        raise HTTPException(status_code=404, detail="Holding not found")
    return h


@router.patch("/{holding_id}", response_model=HoldingOut)
def update_holding_endpoint(
    holding_id: int,
    payload: HoldingUpdate,
    db: Session = Depends(get_db),
):
    """Update a holding."""
    h = update_holding(db, holding_id, payload)
    if not h:
        raise HTTPException(status_code=404, detail="Holding not found")
    return h


@router.get("/summary", response_model=HoldingsSummary)
def summarize_holdings_endpoint(
    db: Session = Depends(get_db),
):
    """Get summary of all holdings by type and jurisdiction."""
    return summarize_holdings(db)
