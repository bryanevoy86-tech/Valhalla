"""
Service functions for lead source management.
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session

from app.models.lead_source import LeadSource
from app.models.raw_lead import RawLead
from app.models.normalized_lead import NormalizedLead
from app.schemas.lead_engine import (
    LeadSourceCreate,
    LeadSourceUpdate,
    NormalizedLeadCreate,
)
import hashlib
import json


# ===== LEAD SOURCE OPERATIONS =====

def create_lead_source(db: Session, source: LeadSourceCreate) -> LeadSource:
    """Create a new lead source"""
    db_source = LeadSource(
        name=source.name,
        source_type=source.source_type,
        sector=source.sector,
        base_url=source.base_url,
        scrape_frequency=source.scrape_frequency,
        auth_type=source.auth_type,
        parser_type=source.parser_type,
        status="inactive",
        notes=source.notes,
    )
    db.add(db_source)
    db.commit()
    db.refresh(db_source)
    return db_source


def get_lead_source(db: Session, source_id: int) -> Optional[LeadSource]:
    """Get a lead source by ID"""
    return db.query(LeadSource).filter(LeadSource.id == source_id).first()


def get_lead_sources(db: Session, skip: int = 0, limit: int = 100) -> List[LeadSource]:
    """Get all lead sources with pagination"""
    return db.query(LeadSource).offset(skip).limit(limit).all()


def update_lead_source(
    db: Session, source_id: int, source: LeadSourceUpdate
) -> Optional[LeadSource]:
    """Update a lead source"""
    db_source = get_lead_source(db, source_id)
    if not db_source:
        return None
    
    # Update only provided fields
    update_data = source.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_source, field, value)
    
    db_source.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_source)
    return db_source


def delete_lead_source(db: Session, source_id: int) -> bool:
    """Delete a lead source"""
    db_source = get_lead_source(db, source_id)
    if not db_source:
        return False
    db.delete(db_source)
    db.commit()
    return True


# ===== RAW LEAD OPERATIONS =====

def _compute_hash(data: dict) -> str:
    """Compute SHA256 hash of raw data"""
    json_str = json.dumps(data, sort_keys=True)
    return hashlib.sha256(json_str.encode()).hexdigest()


def ingest_raw_lead(
    db: Session, source_id: int, raw_data: dict
) -> RawLead:
    """Ingest a raw lead from external source"""
    raw_hash = _compute_hash(raw_data)
    
    # Check if we've already seen this exact payload
    existing = db.query(RawLead).filter(
        RawLead.source_id == source_id,
        RawLead.raw_hash == raw_hash,
    ).first()
    
    if existing:
        return existing
    
    db_raw = RawLead(
        source_id=source_id,
        raw_hash=raw_hash,
        raw_data=raw_data,
        status="pending",
    )
    db.add(db_raw)
    db.commit()
    db.refresh(db_raw)
    return db_raw


def get_raw_lead(db: Session, raw_lead_id: int) -> Optional[RawLead]:
    """Get a raw lead by ID"""
    return db.query(RawLead).filter(RawLead.id == raw_lead_id).first()


# ===== NORMALIZED LEAD OPERATIONS =====

def create_normalized_lead(
    db: Session, lead: NormalizedLeadCreate
) -> NormalizedLead:
    """Create a normalized lead"""
    db_lead = NormalizedLead(
        source_id=lead.source_id,
        external_id=lead.external_id,
        full_name=lead.full_name,
        company_name=lead.company_name,
        phone=lead.phone,
        email=lead.email,
        address=lead.address,
        city=lead.city,
        market=lead.market,
        lead_type=lead.lead_type,
        asking_price=lead.asking_price,
        tags=lead.tags or [],
        status="new",
    )
    db.add(db_lead)
    db.commit()
    db.refresh(db_lead)
    return db_lead


def get_normalized_lead(db: Session, lead_id: int) -> Optional[NormalizedLead]:
    """Get a normalized lead by ID"""
    return db.query(NormalizedLead).filter(NormalizedLead.id == lead_id).first()


def get_normalized_leads(
    db: Session, source_id: Optional[int] = None, skip: int = 0, limit: int = 100
) -> List[NormalizedLead]:
    """Get normalized leads with optional filtering"""
    query = db.query(NormalizedLead)
    if source_id:
        query = query.filter(NormalizedLead.source_id == source_id)
    return query.offset(skip).limit(limit).all()


def update_normalized_lead(
    db: Session, lead_id: int, updates: dict
) -> Optional[NormalizedLead]:
    """Update a normalized lead"""
    db_lead = get_normalized_lead(db, lead_id)
    if not db_lead:
        return None
    
    for field, value in updates.items():
        if hasattr(db_lead, field):
            setattr(db_lead, field, value)
    
    db_lead.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_lead)
    return db_lead


# ===== INGESTION HELPERS =====

def normalize_lead_from_raw(
    db: Session, raw_lead: RawLead
) -> NormalizedLead:
    """
    Parse and normalize a raw lead.
    
    This is a basic implementation that extracts common fields.
    Specific scrapers should override this with source-specific logic.
    """
    raw_data = raw_lead.raw_data
    
    # Basic field extraction - customize per source type
    source = get_lead_source(db, raw_lead.source_id)
    
    lead_data = NormalizedLeadCreate(
        source_id=raw_lead.source_id,
        external_id=raw_data.get("id") or raw_data.get("external_id"),
        full_name=raw_data.get("name") or raw_data.get("full_name") or raw_data.get("contact"),
        company_name=raw_data.get("company") or raw_data.get("business_name"),
        phone=raw_data.get("phone") or raw_data.get("contact_phone"),
        email=raw_data.get("email") or raw_data.get("contact_email"),
        address=raw_data.get("address") or raw_data.get("location"),
        city=raw_data.get("city"),
        market=raw_data.get("market") or raw_data.get("area"),
        lead_type=raw_data.get("type") or raw_data.get("lead_type"),
        asking_price=raw_data.get("price") or raw_data.get("asking_price"),
        tags=raw_data.get("tags", []),
    )
    
    # Create the normalized lead
    normalized = create_normalized_lead(db, lead_data)
    
    # Mark raw lead as normalized
    raw_lead.status = "normalized"
    db.commit()
    
    return normalized
