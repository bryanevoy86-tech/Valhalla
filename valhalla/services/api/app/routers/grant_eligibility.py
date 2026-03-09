"""
PACK SA: Grant Eligibility Engine Router
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.db import get_db
from app.schemas.grant_eligibility import (
    GrantProfileSchema,
    EligibilityChecklistSchema,
    ChecklistStatusResponse,
)
from app.services.grant_eligibility import (
    create_grant_profile,
    get_grant_profile,
    get_all_grant_profiles,
    update_grant_profile,
    create_checklist_item,
    get_checklist_for_grant,
    mark_requirement_completed,
    get_checklist_status,
)

router = APIRouter(prefix="/grants", tags=["PACK SA: Grant Eligibility"])


@router.post("/profiles", response_model=GrantProfileSchema)
def create_profile(profile: GrantProfileSchema, db: Session = Depends(get_db)):
    """Create a new grant eligibility profile."""
    return create_grant_profile(db, profile)


@router.get("/profiles", response_model=List[GrantProfileSchema])
def list_profiles(db: Session = Depends(get_db)):
    """Get all grant profiles."""
    return get_all_grant_profiles(db)


@router.get("/profiles/{grant_id}", response_model=GrantProfileSchema)
def get_profile(grant_id: str, db: Session = Depends(get_db)):
    """Get a specific grant profile."""
    profile = get_grant_profile(db, grant_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Grant profile not found")
    return profile


@router.patch("/profiles/{grant_id}")
def update_profile(grant_id: str, updates: dict, db: Session = Depends(get_db)):
    """Update a grant profile."""
    updated = update_grant_profile(db, grant_id, updates)
    if not updated:
        raise HTTPException(status_code=404, detail="Grant profile not found")
    return updated


@router.post("/checklists", response_model=EligibilityChecklistSchema)
def create_checklist(item: EligibilityChecklistSchema, db: Session = Depends(get_db)):
    """Add a requirement to a checklist."""
    return create_checklist_item(db, item)


@router.get("/checklists/{grant_profile_id}", response_model=List[EligibilityChecklistSchema])
def get_checklist(grant_profile_id: int, db: Session = Depends(get_db)):
    """Get all checklist items for a grant."""
    return get_checklist_for_grant(db, grant_profile_id)


@router.post("/checklists/{checklist_item_id}/complete")
def mark_complete(checklist_item_id: int, uploaded: bool = False, db: Session = Depends(get_db)):
    """Mark a requirement as completed."""
    updated = mark_requirement_completed(db, checklist_item_id, uploaded)
    if not updated:
        raise HTTPException(status_code=404, detail="Checklist item not found")
    return {"status": "completed", "item": updated}


@router.get("/status/{grant_profile_id}", response_model=ChecklistStatusResponse)
def get_status(grant_profile_id: int, db: Session = Depends(get_db)):
    """Get progress status for a grant profile."""
    return get_checklist_status(db, grant_profile_id)
