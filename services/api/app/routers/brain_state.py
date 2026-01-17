"""
PACK AL: Brain State Snapshot Router
Prefix: /brain-state
"""

from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.brain_state import BrainStateCreate, BrainStateOut
from app.services.brain_state import create_brain_state, list_brain_states, brain_state_to_dict

router = APIRouter(prefix="/brain-state", tags=["BrainState"])


@router.post("/", response_model=BrainStateOut)
def create_brain_state_endpoint(
    payload: BrainStateCreate,
    db: Session = Depends(get_db),
):
    """Create a new brain state snapshot."""
    obj = create_brain_state(db, payload)
    data = brain_state_to_dict(obj)
    return BrainStateOut(**data)


@router.get("/", response_model=List[BrainStateOut])
def list_brain_states_endpoint(
    limit: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """List brain state snapshots."""
    objs = list_brain_states(db, limit=limit)
    return [BrainStateOut(**brain_state_to_dict(o)) for o in objs]
