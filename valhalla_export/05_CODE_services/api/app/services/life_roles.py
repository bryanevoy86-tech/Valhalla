"""
PACK TE: Life Roles & Capacity Engine Service Layer
"""

from sqlalchemy.orm import Session
from app.models.life_roles import LifeRole, RoleCapacitySnapshot
from app.schemas.life_roles import LifeRoleCreate, RoleCapacityCreate


def create_life_role(db: Session, role: LifeRoleCreate) -> LifeRole:
    """Create a new life role."""
    db_role = LifeRole(
        name=role.name,
        domain=role.domain,
        description=role.description,
        priority=role.priority,
    )
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role


def list_life_roles(db: Session, skip: int = 0, limit: int = 100) -> list[LifeRole]:
    """List all life roles."""
    return db.query(LifeRole).offset(skip).limit(limit).all()


def get_life_role(db: Session, role_id: int) -> LifeRole | None:
    """Get a specific life role by ID."""
    return db.query(LifeRole).filter(LifeRole.id == role_id).first()


def create_capacity_snapshot(
    db: Session, snapshot: RoleCapacityCreate
) -> RoleCapacitySnapshot:
    """Create a new capacity snapshot for a role."""
    db_snapshot = RoleCapacitySnapshot(
        role_id=snapshot.role_id,
        date=snapshot.date,
        load_level=snapshot.load_level,
        notes=snapshot.notes,
    )
    db.add(db_snapshot)
    db.commit()
    db.refresh(db_snapshot)
    return db_snapshot


def list_capacity_snapshots(
    db: Session, skip: int = 0, limit: int = 100
) -> list[RoleCapacitySnapshot]:
    """List all capacity snapshots."""
    return db.query(RoleCapacitySnapshot).offset(skip).limit(limit).all()


def get_capacity_snapshots_for_role(
    db: Session, role_id: int, skip: int = 0, limit: int = 100
) -> list[RoleCapacitySnapshot]:
    """Get all capacity snapshots for a specific role."""
    return (
        db.query(RoleCapacitySnapshot)
        .filter(RoleCapacitySnapshot.role_id == role_id)
        .offset(skip)
        .limit(limit)
        .all()
    )
