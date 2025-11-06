"""
Router for Advanced Negotiation Techniques (Pack 32).
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.advanced_negotiation.schemas import (
    NegotiationTechniqueCreate,
    NegotiationTechniqueOut,
    TechniqueRankingRequest,
)
from app.advanced_negotiation.service import (
    create_technique,
    get_all_techniques,
    get_technique_by_id,
    get_techniques_by_type,
    get_top_techniques,
    update_technique_score,
)

router = APIRouter(prefix="/advanced-negotiation-techniques", tags=["advanced-negotiation-techniques"])


@router.post("/", response_model=NegotiationTechniqueOut, status_code=201)
async def add_technique(technique: NegotiationTechniqueCreate, db: Session = Depends(get_db)):
    """Create a new negotiation technique with effectiveness scoring."""
    return create_technique(db=db, technique=technique)


@router.get("/", response_model=List[NegotiationTechniqueOut])
async def list_techniques(
    technique_type: str | None = Query(None, description="Filter by technique type"),
    db: Session = Depends(get_db),
):
    """List all negotiation techniques, optionally filtered by type."""
    if technique_type:
        return get_techniques_by_type(db=db, technique_type=technique_type)
    return get_all_techniques(db=db)


@router.get("/top", response_model=List[NegotiationTechniqueOut])
async def get_top_ranked(
    min_score: float = Query(70.0, ge=0.0, le=100.0, description="Minimum effectiveness score"),
    limit: int = Query(10, ge=1, le=50, description="Max number of results"),
    db: Session = Depends(get_db),
):
    """Get top-ranked techniques by effectiveness score."""
    return get_top_techniques(db=db, min_score=min_score, limit=limit)


@router.get("/{technique_id}", response_model=NegotiationTechniqueOut)
async def get_technique(technique_id: int, db: Session = Depends(get_db)):
    """Get a specific technique by ID."""
    technique = get_technique_by_id(db=db, technique_id=technique_id)
    if not technique:
        raise HTTPException(status_code=404, detail="Technique not found")
    return technique


@router.put("/{technique_id}/score", response_model=NegotiationTechniqueOut)
async def update_score(
    technique_id: int,
    new_score: float = Query(..., ge=0.0, le=100.0, description="New effectiveness score"),
    db: Session = Depends(get_db),
):
    """Update technique effectiveness score based on AI analysis or feedback."""
    updated = update_technique_score(db=db, technique_id=technique_id, new_score=new_score)
    if not updated:
        raise HTTPException(status_code=404, detail="Technique not found")
    return updated
