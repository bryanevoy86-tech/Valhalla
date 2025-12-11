"""
PACK L0-09: Trajectory Service
Long-term trajectory planning and projection services.
"""

from typing import Optional, List, Tuple
from sqlalchemy.orm import Session

from app.models.trajectory import Trajectory
from app.schemas.trajectory import TrajectoryCreate, TrajectoryUpdate


def create_trajectory(
    db: Session,
    tenant_id: str,
    payload: TrajectoryCreate,
) -> Trajectory:
    """Create a new trajectory for a tenant."""
    trajectory = Trajectory(
        tenant_id=tenant_id,
        **payload.model_dump()
    )
    db.add(trajectory)
    db.commit()
    db.refresh(trajectory)
    return trajectory


def get_current_trajectory(db: Session, tenant_id: str) -> Optional[Trajectory]:
    """Get the most recent trajectory for a tenant."""
    return (
        db.query(Trajectory)
        .filter(Trajectory.tenant_id == tenant_id)
        .order_by(Trajectory.updated_at.desc())
        .first()
    )


def list_trajectories(
    db: Session,
    tenant_id: str,
    skip: int = 0,
    limit: int = 50,
) -> Tuple[List[Trajectory], int]:
    """List trajectories for a tenant with pagination."""
    query = db.query(Trajectory).filter(Trajectory.tenant_id == tenant_id)
    total = query.count()
    items = query.order_by(Trajectory.updated_at.desc()).offset(skip).limit(limit).all()
    return items, total


def update_trajectory(
    db: Session,
    trajectory_id: int,
    payload: TrajectoryUpdate,
) -> Optional[Trajectory]:
    """Update an existing trajectory."""
    trajectory = db.query(Trajectory).filter(Trajectory.id == trajectory_id).first()
    if not trajectory:
        return None
    
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(trajectory, field, value)
    
    db.commit()
    db.refresh(trajectory)
    return trajectory


def recalc_trajectory(
    db: Session,
    tenant_id: str,
    current_state: dict,
    inputs: dict,
) -> Trajectory:
    """
    Recalculate trajectory based on current state and decision inputs.
    This is called after important decisions are executed.
    """
    # Get or create trajectory
    trajectory = get_current_trajectory(db, tenant_id)
    
    if not trajectory:
        # Create a new one with defaults
        trajectory = create_trajectory(
            db,
            tenant_id,
            TrajectoryCreate(
                horizon="12m",
                target_state={"description": "Not yet defined"},
                current_projection={"description": "Calculating..."},
            )
        )
    
    # Update projection based on new inputs
    trajectory.current_projection = {
        "description": inputs.get("description", ""),
        "confidence": inputs.get("confidence", 0.5),
        "key_metrics": inputs.get("key_metrics", {}),
        "risks": inputs.get("risks", []),
    }
    
    # Update roadmap if provided
    if "roadmap" in inputs:
        trajectory.roadmap = inputs["roadmap"]
    
    if "risk_factors" in inputs:
        trajectory.risk_factors = inputs["risk_factors"]
    
    db.commit()
    db.refresh(trajectory)
    return trajectory


def delete_trajectory(db: Session, trajectory_id: int) -> bool:
    """Delete a trajectory."""
    trajectory = db.query(Trajectory).filter(Trajectory.id == trajectory_id).first()
    if not trajectory:
        return False
    
    db.delete(trajectory)
    db.commit()
    return True
