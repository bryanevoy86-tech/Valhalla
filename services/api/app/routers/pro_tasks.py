# services/api/app/routers/pro_tasks.py

from __future__ import annotations

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.pro_task_link import (
    ProfessionalTaskLinkIn,
    ProfessionalTaskLinkOut,
)
from app.services.pro_task_service import (
    create_link,
    update_status,
    list_for_professional,
    list_for_deal,
    get_link,
)

router = APIRouter(
    prefix="/pros/tasks",
    tags=["Professionals", "Tasks"]
)


@router.post("/", response_model=ProfessionalTaskLinkOut, status_code=status.HTTP_201_CREATED)
def link_task(payload: ProfessionalTaskLinkIn, db: Session = Depends(get_db)):
    """Link a task to a professional for tracking."""
    obj = create_link(db, payload)
    return obj


@router.patch("/{link_id}/status", response_model=ProfessionalTaskLinkOut)
def change_status(
    link_id: int,
    status: str = Query(..., description="New status: open, in_progress, blocked, done"),
    db: Session = Depends(get_db)
):
    """Update the status of a task link."""
    obj = update_status(db, link_id, status)
    if not obj:
        raise HTTPException(status_code=404, detail="Link not found")
    return obj


@router.get("/{link_id}", response_model=ProfessionalTaskLinkOut)
def get_task_link(link_id: int, db: Session = Depends(get_db)):
    """Get a specific task link by ID."""
    obj = get_link(db, link_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Link not found")
    return obj


@router.get("/by-professional/{professional_id}", response_model=List[ProfessionalTaskLinkOut])
def get_for_professional(professional_id: int, db: Session = Depends(get_db)):
    """Get all tasks assigned to a specific professional."""
    return list_for_professional(db, professional_id)


@router.get("/by-deal/{deal_id}", response_model=List[ProfessionalTaskLinkOut])
def get_for_deal(deal_id: int, db: Session = Depends(get_db)):
    """Get all tasks linked to a specific deal."""
    return list_for_deal(db, deal_id)
