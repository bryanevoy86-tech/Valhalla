"""Negotiation Memory Router"""
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db

from . import schemas, service

router = APIRouter(prefix="/negotiation/memory", tags=["negotiation_memory"])


@router.post("/", response_model=schemas.NegotiationOutcomeRead)
def log_outcome(
    payload: schemas.NegotiationOutcomeCreate,
    db: Session = Depends(get_db),
):
    """Log a negotiation outcome for learning."""
    o = service.record_outcome(db, payload)
    return schemas.NegotiationOutcomeRead.model_validate(o)


@router.get("/stats", response_model=List[schemas.NegotiationStats])
def get_stats(db: Session = Depends(get_db)):
    """Get negotiation statistics by category and style."""
    return service.compute_stats(db)
