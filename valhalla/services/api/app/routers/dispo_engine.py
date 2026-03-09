"""
PACK Y: Dispo Engine Router
Prefix: /dispo
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.dispo import (
    DispoBuyerCreate,
    DispoBuyerUpdate,
    DispoBuyerOut,
    DispoAssignmentCreate,
    DispoAssignmentUpdate,
    DispoAssignmentOut,
)
from app.services.dispo_engine import (
    create_buyer,
    update_buyer,
    list_buyers,
    get_buyer,
    create_assignment,
    update_assignment,
    list_assignments_for_pipeline,
)

router = APIRouter(prefix="/dispo", tags=["Dispo"])


@router.post("/buyers", response_model=DispoBuyerOut)
def create_buyer_endpoint(
    payload: DispoBuyerCreate,
    db: Session = Depends(get_db),
):
    """Create a new dispo buyer profile."""
    return create_buyer(db, payload)


@router.get("/buyers", response_model=List[DispoBuyerOut])
def list_buyers_endpoint(
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
):
    """List dispo buyer profiles."""
    return list_buyers(db, active_only=active_only)


@router.get("/buyers/{buyer_id}", response_model=DispoBuyerOut)
def get_buyer_endpoint(
    buyer_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific dispo buyer profile."""
    buyer = get_buyer(db, buyer_id)
    if not buyer:
        raise HTTPException(status_code=404, detail="Buyer not found")
    return buyer


@router.patch("/buyers/{buyer_id}", response_model=DispoBuyerOut)
def update_buyer_endpoint(
    buyer_id: int,
    payload: DispoBuyerUpdate,
    db: Session = Depends(get_db),
):
    """Update a dispo buyer profile."""
    buyer = update_buyer(db, buyer_id, payload)
    if not buyer:
        raise HTTPException(status_code=404, detail="Buyer not found")
    return buyer


@router.post("/assignments", response_model=DispoAssignmentOut)
def create_assignment_endpoint(
    payload: DispoAssignmentCreate,
    db: Session = Depends(get_db),
):
    """Create a new dispo assignment."""
    return create_assignment(db, payload)


@router.patch("/assignments/{assignment_id}", response_model=DispoAssignmentOut)
def update_assignment_endpoint(
    assignment_id: int,
    payload: DispoAssignmentUpdate,
    db: Session = Depends(get_db),
):
    """Update a dispo assignment."""
    obj = update_assignment(db, assignment_id, payload)
    if not obj:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return obj


@router.get(
    "/assignments/by-pipeline/{pipeline_id}",
    response_model=List[DispoAssignmentOut],
)
def list_assignments_for_pipeline_endpoint(
    pipeline_id: int,
    db: Session = Depends(get_db),
):
    """List dispo assignments for a wholesale pipeline."""
    return list_assignments_for_pipeline(db, pipeline_id)
