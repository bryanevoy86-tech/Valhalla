"""PACK 70: Contractor Packet Router
API endpoints for contractor packet generation and retrieval.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional

from app.core.db import get_db
from app.services.contractor_packet_service import create_packet, list_packets
from app.schemas.contractor_packet import ContractorPacketOut

router = APIRouter(prefix="/contractor-packet", tags=["Contractor Packet"])


@router.post("/", response_model=ContractorPacketOut)
def new_packet(
    blueprint_id: int,
    material_list: str,
    task_breakdown: str,
    notes: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Create a new contractor packet."""
    return create_packet(db, blueprint_id, material_list, task_breakdown, notes)


@router.get("/", response_model=list[ContractorPacketOut])
def get_packets(blueprint_id: Optional[int] = None, db: Session = Depends(get_db)):
    """Get contractor packets, optionally filtered by blueprint ID."""
    return list_packets(db, blueprint_id)
