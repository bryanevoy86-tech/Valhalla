"""
Lead service logic for Advanced Lead Scraper (Pack 31).

Handles lead creation, retrieval, and status updates aligned with canonical schema.
"""
from sqlalchemy.orm import Session
from datetime import datetime
from app.leads.models import Lead
from app.leads.schemas import LeadCreate


def create_lead(db: Session, lead: LeadCreate) -> Lead:
    """Create a new lead with contact and property information."""
    db_lead = Lead(
        lead_name=lead.lead_name,
        lead_email=lead.lead_email,
        lead_phone=lead.lead_phone,
        property_address=lead.property_address,
        property_city=lead.property_city,
        property_state=lead.property_state,
        property_zip=lead.property_zip,
        estimated_arv=lead.estimated_arv,
        source=lead.source,
        lead_status=lead.lead_status or "new",
        notes=lead.notes,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(db_lead)
    db.commit()
    db.refresh(db_lead)
    return db_lead


def get_all_leads(db: Session, skip: int = 0, limit: int = 100) -> list[Lead]:
    """Retrieve all leads with pagination."""
    return db.query(Lead).offset(skip).limit(limit).all()


def get_lead_by_id(db: Session, lead_id: int) -> Lead | None:
    """Get a specific lead by ID."""
    return db.query(Lead).filter(Lead.id == lead_id).first()


def get_leads_by_status(db: Session, lead_status: str) -> list[Lead]:
    """Filter leads by status."""
    return db.query(Lead).filter(Lead.lead_status == lead_status).all()


def update_lead_status(db: Session, lead_id: int, lead_status: str) -> Lead | None:
    """Update lead qualification status."""
    db_lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not db_lead:
        return None
    setattr(db_lead, "lead_status", lead_status)
    setattr(db_lead, "updated_at", datetime.utcnow())
    db.commit()
    db.refresh(db_lead)
    return db_lead


def delete_lead(db: Session, lead_id: int) -> bool:
    """Delete a lead."""
    db_lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not db_lead:
        return False
    db.delete(db_lead)
    db.commit()
    return True
