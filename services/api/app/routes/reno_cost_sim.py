"""PACK 71: Reno Cost Simulator Router
API endpoints for cost simulation.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional

from app.core.db import get_db
from app.services.reno_cost_sim_service import create_simulation, list_simulations
from app.schemas.reno_cost_sim import RenoCostSimOut

router = APIRouter(prefix="/reno-sim", tags=["Reno Cost Simulator"])


@router.post("/", response_model=RenoCostSimOut)
def new_simulation(
    blueprint_id: int,
    input_payload: str,
    low: float,
    mid: float,
    high: float,
    db: Session = Depends(get_db)
):
    """Create a new cost simulation."""
    return create_simulation(db, blueprint_id, input_payload, low, mid, high)


@router.get("/", response_model=list[RenoCostSimOut])
def get_simulations(blueprint_id: Optional[int] = None, db: Session = Depends(get_db)):
    """Get cost simulations, optionally filtered by blueprint ID."""
    return list_simulations(db, blueprint_id)
