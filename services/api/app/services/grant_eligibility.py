"""
PACK SA: Grant Eligibility Engine Services
"""

from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.grant_eligibility import GrantProfile, EligibilityChecklist
from app.schemas.grant_eligibility import (
    GrantProfileSchema,
    EligibilityChecklistSchema,
    ChecklistStatusResponse,
)


def create_grant_profile(db: Session, profile: GrantProfileSchema) -> GrantProfile:
    """Create a new grant eligibility profile."""
    db_profile = GrantProfile(
        grant_id=profile.grant_id,
        program_name=profile.program_name,
        description=profile.description,
        funding_type=profile.funding_type,
        region=profile.region,
        target_groups=profile.target_groups,
        requirements=profile.requirements,
        status=profile.status,
        notes=profile.notes,
    )
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return db_profile


def get_grant_profile(db: Session, grant_id: str) -> Optional[GrantProfile]:
    """Retrieve a grant profile by grant_id."""
    return db.query(GrantProfile).filter(GrantProfile.grant_id == grant_id).first()


def get_all_grant_profiles(db: Session) -> List[GrantProfile]:
    """Get all grant profiles."""
    return db.query(GrantProfile).all()


def update_grant_profile(db: Session, grant_id: str, updates: dict) -> Optional[GrantProfile]:
    """Update a grant profile."""
    profile = get_grant_profile(db, grant_id)
    if not profile:
        return None
    
    for key, value in updates.items():
        if hasattr(profile, key):
            setattr(profile, key, value)
    
    db.commit()
    db.refresh(profile)
    return profile


def create_checklist_item(db: Session, item: EligibilityChecklistSchema) -> EligibilityChecklist:
    """Create a checklist item for a requirement."""
    db_item = EligibilityChecklist(
        grant_profile_id=item.grant_profile_id,
        requirement_key=item.requirement_key,
        requirement_name=item.requirement_name,
        requirement_type=item.requirement_type,
        is_completed=item.is_completed,
        is_uploaded=item.is_uploaded,
        notes=item.notes,
        uploaded_filename=item.uploaded_filename,
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def get_checklist_for_grant(db: Session, grant_profile_id: int) -> List[EligibilityChecklist]:
    """Get all checklist items for a grant profile."""
    return db.query(EligibilityChecklist).filter(
        EligibilityChecklist.grant_profile_id == grant_profile_id
    ).all()


def mark_requirement_completed(
    db: Session, checklist_item_id: int, uploaded: bool = False
) -> Optional[EligibilityChecklist]:
    """Mark a requirement as completed and optionally as uploaded."""
    item = db.query(EligibilityChecklist).filter(EligibilityChecklist.id == checklist_item_id).first()
    if not item:
        return None
    
    item.is_completed = True
    if uploaded:
        item.is_uploaded = True
    
    db.commit()
    db.refresh(item)
    return item


def get_checklist_status(db: Session, grant_profile_id: int) -> ChecklistStatusResponse:
    """Calculate progress for a grant profile's checklist."""
    items = get_checklist_for_grant(db, grant_profile_id)
    
    total = len(items)
    completed = sum(1 for item in items if item.is_completed)
    uploaded = sum(1 for item in items if item.is_uploaded)
    missing = total - completed
    
    progress = (completed / total * 100) if total > 0 else 0
    
    return ChecklistStatusResponse(
        total_requirements=total,
        completed=completed,
        uploaded=uploaded,
        missing=missing,
        progress_percentage=progress,
    )
