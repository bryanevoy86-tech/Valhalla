"""
PACK AE: Public Investor Module Router
Prefix: /investor
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.investor_module import (
    InvestorProfileCreate,
    InvestorProfileUpdate,
    InvestorProfileOut,
    InvestorProjectCreate,
    InvestorProjectUpdate,
    InvestorProjectOut,
)
from app.services.investor_module import (
    create_or_get_profile,
    update_profile,
    get_profile,
    create_project,
    update_project,
    list_projects,
    get_project_by_slug,
)

router = APIRouter(prefix="/investor", tags=["Investor"])


@router.post("/profile", response_model=InvestorProfileOut)
def create_or_get_profile_endpoint(
    payload: InvestorProfileCreate,
    db: Session = Depends(get_db),
):
    """Create a new investor profile or return existing one"""
    return create_or_get_profile(db, payload)


@router.get("/profile/{user_id}", response_model=Optional[InvestorProfileOut])
def get_profile_endpoint(
    user_id: int,
    db: Session = Depends(get_db),
):
    """Get an investor profile by user_id"""
    return get_profile(db, user_id)


@router.patch("/profile/{user_id}", response_model=InvestorProfileOut)
def update_profile_endpoint(
    user_id: int,
    payload: InvestorProfileUpdate,
    db: Session = Depends(get_db),
):
    """Update an investor profile"""
    obj = update_profile(db, user_id, payload)
    if not obj:
        raise HTTPException(status_code=404, detail="Investor profile not found")
    return obj


@router.post("/projects", response_model=InvestorProjectOut)
def create_project_endpoint(
    payload: InvestorProjectCreate,
    db: Session = Depends(get_db),
):
    """Create a new project summary"""
    return create_project(db, payload)


@router.get("/projects", response_model=List[InvestorProjectOut])
def list_projects_endpoint(
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """List all project summaries, optionally filtered by status"""
    return list_projects(db, status=status)


@router.get("/projects/{slug}", response_model=InvestorProjectOut)
def get_project_endpoint(
    slug: str,
    db: Session = Depends(get_db),
):
    """Get a project summary by slug"""
    obj = get_project_by_slug(db, slug)
    if not obj:
        raise HTTPException(status_code=404, detail="Project not found")
    return obj


@router.patch("/projects/{slug}", response_model=InvestorProjectOut)
def update_project_endpoint(
    slug: str,
    payload: InvestorProjectUpdate,
    db: Session = Depends(get_db),
):
    """Update a project summary by slug"""
    obj = update_project(db, slug, payload)
    if not obj:
        raise HTTPException(status_code=404, detail="Project not found")
    return obj
