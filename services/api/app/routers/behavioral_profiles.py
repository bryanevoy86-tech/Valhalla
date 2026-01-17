"""
Router for AI Behavioral Profiling (Pack 33).
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.behavioral_profiling.schemas import (
    BehavioralProfileCreate,
    BehavioralProfileOut,
    BehavioralProfileUpdate,
    EngagementRecommendation,
)
from app.behavioral_profiling.service import (
    create_behavioral_profile,
    get_all_profiles,
    get_profile_by_user,
    get_profiles_by_engagement,
    update_profile,
    generate_engagement_strategy,
)

router = APIRouter(prefix="/behavioral-profiles", tags=["behavioral-profiles"])


@router.post("/", response_model=BehavioralProfileOut, status_code=201)
async def create_profile(profile: BehavioralProfileCreate, db: Session = Depends(get_db)):
    """Create a new behavioral profile for a user."""
    return create_behavioral_profile(db=db, profile=profile)


@router.get("/", response_model=List[BehavioralProfileOut])
async def list_profiles(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    engagement_level: str | None = Query(None, description="Filter by engagement level"),
    db: Session = Depends(get_db),
):
    """List all behavioral profiles with optional filtering."""
    if engagement_level:
        return get_profiles_by_engagement(db=db, engagement_level=engagement_level)
    return get_all_profiles(db=db, skip=skip, limit=limit)


@router.get("/user/{user_id}", response_model=BehavioralProfileOut)
async def get_user_profile(user_id: int, db: Session = Depends(get_db)):
    """Get behavioral profile for a specific user."""
    profile = get_profile_by_user(db=db, user_id=user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found for this user")
    return profile


@router.put("/{profile_id}", response_model=BehavioralProfileOut)
async def update_user_profile(
    profile_id: int,
    update_data: BehavioralProfileUpdate,
    db: Session = Depends(get_db),
):
    """Update an existing behavioral profile."""
    updated = update_profile(db=db, profile_id=profile_id, update_data=update_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Profile not found")
    return updated


@router.get("/strategy/{user_id}", response_model=EngagementRecommendation)
async def get_engagement_strategy(user_id: int, db: Session = Depends(get_db)):
    """
    Get AI-driven engagement strategy recommendation for a user.
    Returns personalized strategy based on behavioral analysis.
    """
    strategy = generate_engagement_strategy(db=db, user_id=user_id)
    if not strategy:
        raise HTTPException(status_code=404, detail="No profile found for this user")
    return strategy
