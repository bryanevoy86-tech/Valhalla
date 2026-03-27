"""
Lead router for HTTP API endpoints.

Exposes CRUD operations for Lead management with audit logging.
Canonical lead schema: lead_name, lead_email, lead_phone, property_*, estimated_arv, source, lead_status
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.db import get_db
from app.leads.models import Lead
from app.leads.schemas import LeadCreate, LeadOut, LeadStatusUpdate
from app.leads import service as lead_service

router = APIRouter(prefix="/leads", tags=["leads"])


@router.post("", response_model=LeadOut, status_code=status.HTTP_201_CREATED)
async def create_lead(lead: LeadCreate, db: Session = Depends(get_db)):
    """Create a new lead with contact and property information."""
    db_lead = lead_service.create_lead(db, lead)
    
    # Log to audit_logs table
    try:
        from sqlalchemy import text
        db.execute(text("""
            INSERT INTO audit_logs (entity_type, entity_id, action, new_value, notes, created_at)
            VALUES (:entity_type, :entity_id, :action, :new_value, :notes, :created_at)
        """), {
            "entity_type": "lead",
            "entity_id": db_lead.id,
            "action": "created",
            "new_value": f'{{"name": "{db_lead.lead_name}", "email": "{db_lead.lead_email}", "source": "{db_lead.source}", "status": "{db_lead.lead_status}"}}',
            "notes": f"New lead from {db_lead.source}: {db_lead.lead_name}",
            "created_at": datetime.utcnow()
        })
        db.commit()
    except Exception as e:
        # Log audit failures but don't fail the request
        print(f"Audit log failed: {e}")
    
    return db_lead


@router.get("", response_model=list[LeadOut])
async def list_leads(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all leads with pagination."""
    return lead_service.get_all_leads(db, skip=skip, limit=limit)


@router.get("/{lead_id}", response_model=LeadOut)
async def get_lead(lead_id: int, db: Session = Depends(get_db)):
    """Get a specific lead by ID."""
    db_lead = lead_service.get_lead_by_id(db, lead_id)
    if not db_lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
    return db_lead


@router.patch("/{lead_id}", response_model=LeadOut)
async def update_lead_status(lead_id: int, update: LeadStatusUpdate, db: Session = Depends(get_db)):
    """Update lead status."""
    db_lead = lead_service.get_lead_by_id(db, lead_id)
    if not db_lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
    
    old_status = db_lead.lead_status
    db_lead = lead_service.update_lead_status(db, lead_id, update.lead_status)
    
    # Log status change
    try:
        from sqlalchemy import text
        db.execute(text("""
            INSERT INTO audit_logs (entity_type, entity_id, action, previous_value, new_value, notes, created_at)
            VALUES (:entity_type, :entity_id, :action, :previous_value, :new_value, :notes, :created_at)
        """), {
            "entity_type": "lead",
            "entity_id": lead_id,
            "action": "status_updated",
            "previous_value": f'{{"status": "{old_status}"}}',
            "new_value": f'{{"status": "{update.lead_status}"}}',
            "notes": f"Lead status changed from {old_status} to {update.lead_status}",
            "created_at": datetime.utcnow()
        })
        db.commit()
    except Exception as e:
        print(f"Audit log failed: {e}")
    
    return db_lead
