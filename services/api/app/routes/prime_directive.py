"""PACK 61: Prime Directive Router
API endpoints for prime directive operations.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.services.prime_directive_service import save_prime_directive, get_active_directive
from app.schemas.prime_directive import PrimeDirectiveOut

router = APIRouter(prefix="/prime-directive", tags=["Prime Directive"])


@router.post("/", response_model=PrimeDirectiveOut)
def set_prime_directive(directive: str, db: Session = Depends(get_db)):
    """Set a new prime directive."""
    return save_prime_directive(db, directive)


@router.get("/", response_model=PrimeDirectiveOut)
def fetch_active_directive(db: Session = Depends(get_db)):
    """Fetch the currently active prime directive."""
    return get_active_directive(db)
