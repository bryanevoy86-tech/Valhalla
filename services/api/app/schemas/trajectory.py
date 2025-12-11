"""
PACK L0-09: Trajectory Schemas
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class TrajectoryBase(BaseModel):
    """Base schema for trajectories."""
    horizon: str = Field(default="12m", description="Time horizon: 3m, 6m, 12m, 3y, 5y, 10y")
    target_state: Dict[str, Any] = Field(..., description="Where we want to be")
    current_projection: Dict[str, Any] = Field(..., description="Where we're headed")
    roadmap: Optional[List[Dict[str, Any]]] = Field(default=[], description="Milestones to reach target")
    risk_factors: Optional[List[Dict[str, Any]]] = Field(default=[], description="Identified risks")


class TrajectoryCreate(TrajectoryBase):
    """Schema for creating a trajectory."""
    pass


class TrajectoryUpdate(BaseModel):
    """Schema for updating a trajectory."""
    horizon: Optional[str] = None
    target_state: Optional[Dict[str, Any]] = None
    current_projection: Optional[Dict[str, Any]] = None
    roadmap: Optional[List[Dict[str, Any]]] = None
    risk_factors: Optional[List[Dict[str, Any]]] = None


class TrajectoryOut(TrajectoryBase):
    """Schema for outputting a trajectory."""
    id: int
    tenant_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TrajectoryList(BaseModel):
    """Paginated list of trajectories."""
    total: int
    items: List[TrajectoryOut]
    created_at: datetime

    class Config:
        from_attributes = True


class TrajectorySnapshotIn(BaseModel):
    target_id: int
    current_value: float
    expected_value: float
    details: Optional[Dict[str, Any]] = None


class TrajectorySnapshotOut(BaseModel):
    id: int
    target_id: int
    current_value: float
    deviation: float
    status: str
    details: Optional[Dict[str, Any]]
    taken_at: datetime

    class Config:
        from_attributes = True


class TrajectorySnapshotList(BaseModel):
    total: int
    items: List[TrajectorySnapshotOut]
