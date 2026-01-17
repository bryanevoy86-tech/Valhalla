"""
PACK L0-09: Trajectory Router
Long-term trajectory planning and projection.
Prefix: /api/v1/trajectory
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.trajectory import (
    TrajectoryCreate,
    TrajectoryUpdate,
    TrajectoryOut,
    TrajectoryList,
)
from app.services import trajectory as service
from app.models.trajectory import Trajectory

router = APIRouter(
    prefix="/api/v1/trajectory",
    tags=["Strategic Engine", "Trajectory"],
)


def get_tenant_id(request) -> str:
    """Extract tenant_id from request context."""
    return "default-tenant"


@router.post("", response_model=TrajectoryOut, status_code=201)
def create_trajectory(
    payload: TrajectoryCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
):
    """Create a new trajectory."""
    return service.create_trajectory(db, tenant_id, payload)


@router.get("", response_model=TrajectoryList)
def list_trajectories(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
):
    """List trajectories for the tenant."""
    items, total = service.list_trajectories(db, tenant_id, skip=skip, limit=limit)
    return TrajectoryList(total=total, items=items)


@router.get("/current", response_model=TrajectoryOut)
def get_current_trajectory(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
):
    """Get the current trajectory for the tenant."""
    trajectory = service.get_current_trajectory(db, tenant_id)
    if not trajectory:
        raise HTTPException(status_code=404, detail="No trajectory found")
    return trajectory


@router.get("/{trajectory_id}", response_model=TrajectoryOut)
def get_trajectory(
    trajectory_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific trajectory."""
    trajectory = db.query(Trajectory).filter(Trajectory.id == trajectory_id).first()
    if not trajectory:
        raise HTTPException(status_code=404, detail="Trajectory not found")
    return trajectory


@router.patch("/{trajectory_id}", response_model=TrajectoryOut)
def update_trajectory(
    trajectory_id: int,
    payload: TrajectoryUpdate,
    db: Session = Depends(get_db),
):
    """Update a trajectory."""
    trajectory = service.update_trajectory(db, trajectory_id, payload)
    if not trajectory:
        raise HTTPException(status_code=404, detail="Trajectory not found")
    return trajectory


@router.post("/{trajectory_id}/recalc", response_model=TrajectoryOut)
def recalc_trajectory(
    trajectory_id: int,
    current_state: dict = {},
    inputs: dict = {},
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
):
    """Recalculate trajectory based on inputs."""
    trajectory = db.query(Trajectory).filter(Trajectory.id == trajectory_id).first()
    if not trajectory:
        raise HTTPException(status_code=404, detail="Trajectory not found")
    
    trajectory = service.recalc_trajectory(db, tenant_id, current_state, inputs)
    return trajectory


@router.delete("/{trajectory_id}", status_code=204)
def delete_trajectory(
    trajectory_id: int,
    db: Session = Depends(get_db),
):
    """Delete a trajectory."""
    success = service.delete_trajectory(db, trajectory_id)
    if not success:
        raise HTTPException(status_code=404, detail="Trajectory not found")
    return None
)

router = APIRouter(prefix="/intelligence/trajectory", tags=["Intelligence", "Trajectory"])


@router.post("/targets", response_model=TrajectoryTargetOut)
def create_target_endpoint(
    payload: TrajectoryTargetIn,
    db: Session = Depends(get_db),
):
    return create_trajectory_target(db, payload)


@router.post("/snapshots", response_model=TrajectorySnapshotOut)
def record_snapshot_endpoint(
    payload: TrajectorySnapshotIn,
    db: Session = Depends(get_db),
):
    return record_snapshot(db, payload)


@router.get("/targets/{target_id}/snapshots", response_model=TrajectorySnapshotList)
def list_snapshots_endpoint(
    target_id: int,
    limit: int = Query(365, ge=1, le=3650),
    db: Session = Depends(get_db),
):
    items = list_snapshots_for_target(db, target_id=target_id, limit=limit)
    return TrajectorySnapshotList(
        total=len(items),
        items=[TrajectorySnapshotOut.model_validate(i) for i in items],
    )
