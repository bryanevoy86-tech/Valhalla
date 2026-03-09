"""
PACK CI5: Heimdall Tuning Ruleset Router
Prefix: /intelligence/tuning
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.tuning_rules import (
    TuningProfileIn,
    TuningProfileOut,
    TuningProfileList,
    TuningConstraintIn,
    TuningConstraintOut,
    TuningConstraintList,
)
from app.services.tuning_rules import (
    upsert_profile,
    list_profiles,
    add_constraint,
    list_constraints_for_profile,
)

router = APIRouter(prefix="/intelligence/tuning", tags=["Intelligence", "Tuning"])


@router.post("/profiles", response_model=TuningProfileOut)
def upsert_profile_endpoint(
    payload: TuningProfileIn,
    db: Session = Depends(get_db),
):
    """Create or update a tuning profile."""
    return upsert_profile(db, payload)


@router.get("/profiles", response_model=TuningProfileList)
def list_profiles_endpoint(
    db: Session = Depends(get_db),
):
    """List all tuning profiles."""
    items = list_profiles(db)
    return TuningProfileList(total=len(items), items=items)


@router.post("/constraints", response_model=TuningConstraintOut)
def add_constraint_endpoint(
    payload: TuningConstraintIn,
    db: Session = Depends(get_db),
):
    """Add a constraint to a profile."""
    return add_constraint(db, payload)


@router.get("/profiles/{profile_id}/constraints", response_model=TuningConstraintList)
def list_constraints_endpoint(
    profile_id: int,
    db: Session = Depends(get_db),
):
    """List all constraints for a profile."""
    items = list_constraints_for_profile(db, profile_id=profile_id)
    return TuningConstraintList(total=len(items), items=items)
