"""PACK 70: Contractor Packet Service
Service layer for contractor packet operations.
"""

from typing import Optional
from sqlalchemy.orm import Session

from app.models.contractor_packet import ContractorPacket


def create_packet(
    db: Session,
    blueprint_id: int,
    material_list: str,
    task_breakdown: str,
    notes: Optional[str]
) -> ContractorPacket:
    """Create a new contractor packet."""
    pkt = ContractorPacket(
        blueprint_id=blueprint_id,
        material_list=material_list,
        task_breakdown=task_breakdown,
        notes=notes
    )
    db.add(pkt)
    db.commit()
    db.refresh(pkt)
    return pkt


def list_packets(db: Session, blueprint_id: Optional[int] = None) -> list:
    """List contractor packets, optionally filtered by blueprint ID."""
    q = db.query(ContractorPacket)
    if blueprint_id:
        q = q.filter(ContractorPacket.blueprint_id == blueprint_id)
    return q.order_by(ContractorPacket.id.desc()).all()
