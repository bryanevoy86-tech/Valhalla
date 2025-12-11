"""PACK 71: Reno Cost Simulator Service
Service layer for renovation cost simulation operations.
"""

from typing import Optional
from sqlalchemy.orm import Session

from app.models.reno_cost_sim import RenoCostSimulation


def create_simulation(
    db: Session,
    blueprint_id: int,
    input_payload: str,
    low: float,
    mid: float,
    high: float
) -> RenoCostSimulation:
    """Create a new cost simulation."""
    sim = RenoCostSimulation(
        blueprint_id=blueprint_id,
        input_payload=input_payload,
        low_estimate=low,
        mid_estimate=mid,
        high_estimate=high
    )
    db.add(sim)
    db.commit()
    db.refresh(sim)
    return sim


def list_simulations(db: Session, blueprint_id: Optional[int] = None) -> list:
    """List cost simulations, optionally filtered by blueprint ID."""
    q = db.query(RenoCostSimulation)
    if blueprint_id:
        q = q.filter(RenoCostSimulation.blueprint_id == blueprint_id)
    return q.order_by(RenoCostSimulation.id.desc()).all()
