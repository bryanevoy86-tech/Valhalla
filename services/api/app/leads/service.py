"""
Lead service logic for Advanced Lead Scraper (Pack 31).
"""
from sqlalchemy.orm import Session
from datetime import datetime
from app.leads.models import Lead
from app.leads.schemas import LeadCreate


def create_lead(db: Session, lead: LeadCreate) -> Lead:
    """Create a new lead."""
    db_lead = Lead(
        name=lead.name,
        email=lead.email,
        phone=lead.phone,
        status=lead.status or "new",
        source=lead.source,
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


def get_leads_by_status(db: Session, status: str) -> list[Lead]:
    """Filter leads by status."""
    return db.query(Lead).filter(Lead.status == status).all()


def update_lead_status(db: Session, lead_id: int, status: str) -> Lead | None:
    """Update lead qualification status."""
    db_lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not db_lead:
        return None
    setattr(db_lead, "status", status)
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
