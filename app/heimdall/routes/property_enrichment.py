from fastapi import APIRouter
from pydantic import BaseModel

from app.heimdall.education.property_enrichment_engine import enrich_property

router = APIRouter(prefix="/heimdall/properties", tags=["Heimdall Property Enrichment"])


class PropertyEnrichmentRequest(BaseModel):
    address: str


@router.post("/enrich")
def enrich_property_route(payload: PropertyEnrichmentRequest):
    """
    Enrich property with official public records data.
    
    Input: Property address
    
    Returns:
    - Property details (year built, size, bedrooms, condition, assessed value)
    - Tax status (delinquency, amount, years)
    - Foreclosure status (in foreclosure, liens, bank owned)
    - Market data (historical sales, comps, estimated current value)
    - Owner information (name, type, mailing address)
    - Distress analysis (signals detected, distress score 0-100)
    - Recommendation (HOT_LEAD, WARM_LEAD, RESEARCH_MORE, PASS)
    - Next action (contact immediately, research more, monitor/pass)
    
    Perfect for driving-for-dollars workflow:
    1. Find address
    2. POST /heimdall/properties/enrich
    3. Get distress signals + owner contact
    4. Decide whether to send letter/email
    """
    return enrich_property(payload.address)
