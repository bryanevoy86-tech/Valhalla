"""
FastAPI router for lead acquisition engine.

Endpoints:
    GET    /lead-sources              - List all lead sources
    POST   /lead-sources              - Create a new lead source
    GET    /lead-sources/{id}         - Get a specific lead source
    PUT    /lead-sources/{id}         - Update a lead source
    DELETE /lead-sources/{id}         - Delete a lead source
    POST   /leads                     - List normalized leads
    GET    /leads/{id}                - Get a specific lead
    PUT    /leads/{id}                - Update a lead
    POST   /lead-sources/{id}/ingest/test  - Test ingestion
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from app.core.db import get_db
from app.models.lead_source import LeadSource
from app.schemas.lead_engine import (
    LeadSourceCreate,
    LeadSourceUpdate,
    LeadSourceResponse,
    NormalizedLeadResponse,
    IngestionTestResponse,
)
from app.services.lead_service import (
    create_lead_source,
    get_lead_source,
    get_lead_sources,
    update_lead_source,
    delete_lead_source,
    get_normalized_lead,
    get_normalized_leads,
    update_normalized_lead,
    ingest_raw_lead,
    normalize_lead_from_raw,
)

router = APIRouter(
    prefix="/api/v1",
    tags=["Lead Engine"]
)


# ===== LEAD SOURCE ENDPOINTS =====

@router.get("/lead-sources", response_model=List[LeadSourceResponse])
def list_lead_sources(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """List all lead sources with pagination"""
    sources = get_lead_sources(db, skip=skip, limit=limit)
    return sources


@router.post("/lead-sources", response_model=LeadSourceResponse, status_code=201)
def create_source(
    source: LeadSourceCreate,
    db: Session = Depends(get_db),
):
    """Create a new lead source"""
    db_source = create_lead_source(db, source)
    return db_source


@router.get("/lead-sources/{source_id}", response_model=LeadSourceResponse)
def get_source(
    source_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific lead source"""
    source = get_lead_source(db, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Lead source not found")
    return source


@router.put("/lead-sources/{source_id}", response_model=LeadSourceResponse)
def update_source(
    source_id: int,
    source: LeadSourceUpdate,
    db: Session = Depends(get_db),
):
    """Update a lead source"""
    db_source = update_lead_source(db, source_id, source)
    if not db_source:
        raise HTTPException(status_code=404, detail="Lead source not found")
    return db_source


@router.delete("/lead-sources/{source_id}", status_code=204)
def delete_source(
    source_id: int,
    db: Session = Depends(get_db),
):
    """Delete a lead source"""
    success = delete_lead_source(db, source_id)
    if not success:
        raise HTTPException(status_code=404, detail="Lead source not found")
    return None


# ===== NORMALIZED LEAD ENDPOINTS =====

@router.get("/leads", response_model=List[NormalizedLeadResponse])
def list_leads(
    source_id: int = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """List normalized leads with optional source filtering"""
    leads = get_normalized_leads(db, source_id=source_id, skip=skip, limit=limit)
    return leads


@router.get("/leads/{lead_id}", response_model=NormalizedLeadResponse)
def get_lead(
    lead_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific normalized lead"""
    lead = get_normalized_lead(db, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.put("/leads/{lead_id}", response_model=NormalizedLeadResponse)
def update_lead(
    lead_id: int,
    updates: dict,
    db: Session = Depends(get_db),
):
    """Update a normalized lead"""
    lead = update_normalized_lead(db, lead_id, updates)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


# ===== INGESTION ENDPOINTS =====

@router.post("/lead-sources/{source_id}/ingest/test", response_model=IngestionTestResponse)
def test_ingestion(
    source_id: int,
    db: Session = Depends(get_db),
):
    """
    Test ingestion for a lead source.
    
    Simulates importing sample data:
    - Ingests 2 sample raw leads
    - Normalizes them
    - Returns status and counts
    """
    source = get_lead_source(db, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Lead source not found")
    
    try:
        # Simulate ingesting sample leads
        sample_leads = [
            {
                "id": "sample_1",
                "name": "John Smith",
                "company": "Smith Properties",
                "phone": "555-0101",
                "email": "john@smithprops.com",
                "address": "123 Main St",
                "city": "Dallas",
                "market": "DFW",
                "lead_type": "wholesaler",
                "price": 250000,
                "tags": ["wholesaler", "active"],
            },
            {
                "id": "sample_2",
                "name": "Jane Doe",
                "company": "Doe Investments",
                "phone": "555-0102",
                "email": "jane@doeinvest.com",
                "address": "456 Oak Ave",
                "city": "Austin",
                "market": "Austin",
                "lead_type": "buyer",
                "price": 500000,
                "tags": ["investor", "cash"],
            },
        ]
        
        raw_leads_imported = 0
        normalized_leads_created = 0
        
        # Ingest and normalize
        for sample_data in sample_leads:
            try:
                raw_lead = ingest_raw_lead(db, source_id, sample_data)
                raw_leads_imported += 1
                
                normalized = normalize_lead_from_raw(db, raw_lead)
                normalized_leads_created += 1
            except Exception as e:
                continue
        
        # Update source status
        source.status = "ok"
        source.last_run_at = source.created_at  # Updated in service
        db.commit()
        
        return IngestionTestResponse(
            source_id=source_id,
            source_name=source.name,
            raw_leads_imported=raw_leads_imported,
            normalized_leads_created=normalized_leads_created,
            status="success",
            message=f"Test ingestion complete: {raw_leads_imported} raw leads, {normalized_leads_created} normalized",
            sample_data=sample_leads[0] if sample_leads else None,
        )
    
    except Exception as e:
        source.status = "error"
        db.commit()
        raise HTTPException(
            status_code=500,
            detail=f"Ingestion test failed: {str(e)}"
        )
