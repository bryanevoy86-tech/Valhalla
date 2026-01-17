"""PACK 63: Evolution Service
Service layer for evolution event operations.
"""

from sqlalchemy.orm import Session

from app.models.evolution import EvolutionEvent


def log_evolution_event(db: Session, trigger: str, description: str) -> EvolutionEvent:
    """Log a system evolution event."""
    event = EvolutionEvent(trigger=trigger, description=description)
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def list_evolution_events(db: Session) -> list:
    """List all evolution events in reverse chronological order."""
    return db.query(EvolutionEvent).order_by(EvolutionEvent.id.desc()).all()
