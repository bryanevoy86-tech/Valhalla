"""
PACK SO: Long-Term Empire Governance Map Router
FastAPI endpoints for role definitions and governance management
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.schemas.empire_governance import (
    EmpireRoleSchema, RoleHierarchySchema, SuccessionPlanSchema,
    EmpireGovernanceMapSchema, GovernanceResponse
)
from app.services.empire_governance import (
    create_empire_role, list_active_roles, get_role_by_name,
    create_role_hierarchy, list_role_hierarchy, create_succession_plan,
    list_succession_plans, create_governance_map, get_latest_governance_map,
    calculate_governance_status
)

router = APIRouter(prefix="/empire", tags=["empire-governance"])


@router.post("/roles", response_model=EmpireRoleSchema)
def add_role(role_data: dict, db: Session = Depends(get_db)):
    """Create an empire role."""
    return create_empire_role(db, **role_data)


@router.get("/roles", response_model=list[EmpireRoleSchema])
def list_roles(db: Session = Depends(get_db)):
    """List all active roles."""
    return list_active_roles(db)


@router.get("/roles/{name}", response_model=EmpireRoleSchema)
def get_role(name: str, db: Session = Depends(get_db)):
    """Get a role by name."""
    role = get_role_by_name(db, name)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return role


@router.post("/hierarchy", response_model=RoleHierarchySchema)
def add_hierarchy(hierarchy_data: dict, db: Session = Depends(get_db)):
    """Define a role hierarchy relationship."""
    return create_role_hierarchy(db, **hierarchy_data)


@router.get("/hierarchy", response_model=list[RoleHierarchySchema])
def get_hierarchy(db: Session = Depends(get_db)):
    """Get role hierarchy."""
    return list_role_hierarchy(db)


@router.post("/succession", response_model=SuccessionPlanSchema)
def add_succession(plan_data: dict, db: Session = Depends(get_db)):
    """Create a succession plan."""
    return create_succession_plan(db, **plan_data)


@router.get("/succession", response_model=list[SuccessionPlanSchema])
def list_plans(db: Session = Depends(get_db)):
    """List all succession plans."""
    return list_succession_plans(db)


@router.post("/governance-map", response_model=EmpireGovernanceMapSchema)
def add_governance_map(map_data: dict, db: Session = Depends(get_db)):
    """Create a governance map snapshot."""
    return create_governance_map(db, **map_data)


@router.get("/governance-map", response_model=EmpireGovernanceMapSchema)
def get_governance_map(db: Session = Depends(get_db)):
    """Get latest governance map."""
    governance_map = get_latest_governance_map(db)
    if not governance_map:
        raise HTTPException(status_code=404, detail="Governance map not found")
    return governance_map


@router.get("/status", response_model=GovernanceResponse)
def get_status(db: Session = Depends(get_db)):
    """Get governance structure status."""
    status = calculate_governance_status(db)
    latest_map = get_latest_governance_map(db)
    return GovernanceResponse(
        total_roles=status["total_roles"],
        governance_version=status["governance_version"],
        active_hierarchy=latest_map.role_graph if latest_map else None,
        succession_plans_count=status["succession_plans"],
        last_updated=status["last_updated"]
    )
