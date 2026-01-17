"""
PACK X: Wholesaling Engine Router
Prefix: /wholesale
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.wholesale import (
    WholesalePipelineCreate,
    WholesalePipelineUpdate,
    WholesalePipelineOut,
    WholesaleActivityLogIn,
    WholesaleActivityLogOut,
)
from app.services.wholesale_engine import (
    create_pipeline,
    update_pipeline,
    get_pipeline,
    list_pipelines,
    log_activity,
)

router = APIRouter(prefix="/wholesale", tags=["Wholesaling"])


@router.post("/", response_model=WholesalePipelineOut)
def create_wholesale_pipeline(
    payload: WholesalePipelineCreate,
    db: Session = Depends(get_db),
):
    """Create a new wholesale pipeline."""
    return create_pipeline(db, payload)


@router.get(
    "/",
    response_model=List[WholesalePipelineOut],
)
def list_wholesale_pipelines(
    stage: Optional[str] = Query(None, description="Filter by pipeline stage"),
    db: Session = Depends(get_db),
):
    """List wholesale pipelines, optionally filtered by stage."""
    return list_pipelines(db, stage=stage)


@router.get("/{pipeline_id}", response_model=WholesalePipelineOut)
def get_wholesale_pipeline(
    pipeline_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific wholesale pipeline."""
    pipe = get_pipeline(db, pipeline_id)
    if not pipe:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return pipe


@router.patch("/{pipeline_id}", response_model=WholesalePipelineOut)
def update_wholesale_pipeline(
    pipeline_id: int,
    payload: WholesalePipelineUpdate,
    db: Session = Depends(get_db),
):
    """Update a wholesale pipeline."""
    pipe = update_pipeline(db, pipeline_id, payload)
    if not pipe:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return pipe


@router.post("/{pipeline_id}/activities", response_model=WholesaleActivityLogOut)
def add_wholesale_activity(
    pipeline_id: int,
    payload: WholesaleActivityLogIn,
    db: Session = Depends(get_db),
):
    """Log an activity on a wholesale pipeline."""
    act = log_activity(db, pipeline_id, payload)
    if not act:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return act
