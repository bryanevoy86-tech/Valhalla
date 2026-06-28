from typing import Any, Dict

from fastapi import APIRouter
from pydantic import BaseModel

from app.heimdall.education.owner_outreach_letter_engine import (
    generate_owner_outreach_packet,
)

router = APIRouter(
    prefix="/heimdall/owner-outreach",
    tags=["Heimdall Owner Outreach"],
)


class OwnerOutreachRequest(BaseModel):
    property_record: Dict[str, Any]


@router.post("/draft-letter")
def draft_letter(payload: OwnerOutreachRequest):
    """
    Generate draft owner outreach letter from property intel record.
    
    Input: property_record with distress_analysis and property_data
    Output: draft_letter (tailored to distress level) + delivery recommendations
    
    Letter types:
    - High distress (75+): Soft help messaging
    - Moderate (50-74): General off-market interest
    - Light (25-49): Gentle followup
    - Below 25: Blocked
    
    All letters are legally compliant, non-threatening, and respectful.
    Requires human approval before sending via POST /message-send-gate.
    """
    return generate_owner_outreach_packet(payload.property_record)
