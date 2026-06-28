from typing import Any, Dict

from fastapi import APIRouter
from pydantic import BaseModel

from app.heimdall.education.document_packet_engine import prepare_deal_packets

router = APIRouter(prefix="/heimdall/documents", tags=["Heimdall Document Packets"])


class DealPacketRequest(BaseModel):
    deal: Dict[str, Any]


@router.post("/prepare-packets")
def prepare_packets(payload: DealPacketRequest):
    """
    Prepare clean document packets for all stakeholders.
    
    Returns packets for:
    - seller_offer_summary: For your records before sending to seller
    - lawyer_review_packet: For lawyer review with questions and red flags
    - buyer_teaser_packet: For buyer outreach (high-level summary)
    - va_task_packet: For VA task assignment and follow-up
    - accounting_packet: For accountant preliminary review
    
    Also includes:
    - missing_documents: Checklist of required documents not yet collected
    - human_approval_required: Always true
    - lawyer_review_required_before_contract: Always true
    """
    return prepare_deal_packets(payload.deal)
