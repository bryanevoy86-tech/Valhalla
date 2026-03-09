"""PACK 63: Evolution Router
API endpoints for system evolution event logging and retrieval.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.services.evolution_service import log_evolution_event, list_evolution_events
from app.schemas.evolution import EvolutionEventOut

router = APIRouter(prefix="/evolution", tags=["Evolution Engine"])


@router.post("/", response_model=EvolutionEventOut)
def add_event(trigger: str, description: str, db: Session = Depends(get_db)):
    """Log a new evolution event."""
    return log_evolution_event(db, trigger, description)


@router.get("/", response_model=list[EvolutionEventOut])
def get_events(db: Session = Depends(get_db)):
    """Get all evolution events."""
    return list_evolution_events(db)
