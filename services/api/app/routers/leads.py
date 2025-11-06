"""
Leads router for Advanced Lead Scraper (Pack 31).
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.leads.schemas import LeadCreate, LeadOut, LeadStatusUpdate
from app.leads.service import (
    create_lead,
    get_all_leads,
    get_lead_by_id,
    get_leads_by_status,
    update_lead_status,
    delete_lead,
)

router = APIRouter(prefix="/leads", tags=["leads"])


@router.post("/", response_model=LeadOut, status_code=201)
async def create_new_lead(lead: LeadCreate, db: Session = Depends(get_db)):
    """Create a new lead."""
    return create_lead(db=db, lead=lead)


@router.get("/", response_model=List[LeadOut])
async def list_leads(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    status: str | None = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
):
    """List all leads with optional status filter and pagination."""
    if status:
        return get_leads_by_status(db=db, status=status)
    return get_all_leads(db=db, skip=skip, limit=limit)


@router.get("/{lead_id}", response_model=LeadOut)
async def get_lead(lead_id: int, db: Session = Depends(get_db)):
    """Get a specific lead by ID."""
    lead = get_lead_by_id(db=db, lead_id=lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.put("/{lead_id}/status", response_model=LeadOut)
async def update_status(
    lead_id: int,
    status_update: LeadStatusUpdate,
    db: Session = Depends(get_db),
):
    """Update lead qualification status."""
    updated_lead = update_lead_status(db=db, lead_id=lead_id, status=status_update.status)
    if not updated_lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return updated_lead


@router.delete("/{lead_id}", status_code=204)
async def remove_lead(lead_id: int, db: Session = Depends(get_db)):
    """Delete a lead."""
    success = delete_lead(db=db, lead_id=lead_id)
    if not success:
        raise HTTPException(status_code=404, detail="Lead not found")
    return None
