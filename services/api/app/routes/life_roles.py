"""
PACK TE: Life Roles & Capacity Engine Router
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.schemas.life_roles import LifeRoleCreate, LifeRoleOut, RoleCapacityCreate, RoleCapacityOut
from app.services.life_roles import (
    create_life_role,
    list_life_roles,
    get_life_role,
    create_capacity_snapshot,
    list_capacity_snapshots,
    get_capacity_snapshots_for_role,
)

router = APIRouter(prefix="/life", tags=["Life Roles & Capacity"])


@router.post("/roles", response_model=LifeRoleOut)
def post_life_role(role: LifeRoleCreate, db: Session = Depends(get_db)):
    """Create a new life role."""
    return create_life_role(db, role)


@router.get("/roles", response_model=list[LifeRoleOut])
def get_life_roles(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all life roles."""
    return list_life_roles(db, skip, limit)


@router.get("/roles/{role_id}", response_model=LifeRoleOut)
def get_one_role(role_id: int, db: Session = Depends(get_db)):
    """Get a specific life role."""
    db_role = get_life_role(db, role_id)
    if not db_role:
        raise HTTPException(status_code=404, detail="Life role not found")
    return db_role


@router.post("/roles/capacity", response_model=RoleCapacityOut)
def post_capacity_snapshot(snapshot: RoleCapacityCreate, db: Session = Depends(get_db)):
    """Record a capacity snapshot for a role."""
    # Verify role exists
    if not get_life_role(db, snapshot.role_id):
        raise HTTPException(status_code=404, detail="Life role not found")
    return create_capacity_snapshot(db, snapshot)


@router.get("/capacity", response_model=list[RoleCapacityOut])
def get_capacity_snapshots(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all capacity snapshots."""
    return list_capacity_snapshots(db, skip, limit)


@router.get("/roles/{role_id}/capacity", response_model=list[RoleCapacityOut])
def get_role_capacity_history(
    role_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    """Get capacity snapshot history for a specific role."""
    # Verify role exists
    if not get_life_role(db, role_id):
        raise HTTPException(status_code=404, detail="Life role not found")
    return get_capacity_snapshots_for_role(db, role_id, skip, limit)
