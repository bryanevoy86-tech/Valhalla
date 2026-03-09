"""PACK 61: Prime Directive Service
Service layer for prime directive operations.
"""

from sqlalchemy.orm import Session

from app.models.prime_directive import PrimeDirective


def save_prime_directive(db: Session, directive: str) -> PrimeDirective:
    """Save a new prime directive."""
    item = PrimeDirective(directive=directive, active=True)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def get_active_directive(db: Session) -> PrimeDirective:
    """Get the currently active prime directive."""
    return db.query(PrimeDirective).filter(PrimeDirective.active == True).first()
