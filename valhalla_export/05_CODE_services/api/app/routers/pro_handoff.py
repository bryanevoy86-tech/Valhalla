# services/api/app/routers/pro_handoff.py

from __future__ import annotations

from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.services.pro_handoff_engine import generate_handoff_packet

router = APIRouter(
    prefix="/pros/handoff",
    tags=["Professionals", "Handoff"]
)


@router.get("/{professional_id}")
def create_handoff_packet(
    professional_id: int,
    deal_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Generate a professional handoff packet for escalation.
    
    Includes professional details, scorecard, and optionally deal/risk summaries.
    """
    try:
        packet = generate_handoff_packet(
            db=db,
            professional_id=professional_id,
            deal_id=deal_id
        )
        return packet
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.post("/{professional_id}")
def create_handoff_packet_with_context(
    professional_id: int,
    context: Dict[str, Any] = Body(...),
    deal_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Generate a professional handoff packet with custom context.
    
    Allows including additional metadata, notes, or instructions.
    """
    try:
        packet = generate_handoff_packet(
            db=db,
            professional_id=professional_id,
            deal_id=deal_id,
            context=context
        )
        return packet
    except ValueError as e:
        raise HTTPException(404, str(e))
