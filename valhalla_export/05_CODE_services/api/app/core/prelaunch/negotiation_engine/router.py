"""Negotiation Engine Router - FREYJA"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db

from .schemas import (
    NegotiationTemplateCreate,
    NegotiationTemplateRead,
    NegotiationRequest,
    NegotiationResponse,
)
from . import service, models

router = APIRouter(prefix="/negotiation", tags=["negotiation"])


@router.post("/template", response_model=NegotiationTemplateRead)
def add_template(payload: NegotiationTemplateCreate, db: Session = Depends(get_db)):
    """Add a new negotiation template."""
    t = models.NegotiationTemplate(**payload.model_dump())
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


@router.post("/run", response_model=NegotiationResponse)
def run(payload: NegotiationRequest, db: Session = Depends(get_db)):
    """Run a negotiation script based on category and tone."""
    return service.run_negotiation(db, payload)
