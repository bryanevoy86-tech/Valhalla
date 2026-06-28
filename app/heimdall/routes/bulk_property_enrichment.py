from typing import Any, Dict, List

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.heimdall.services.bulk_property_enrichment_service import (
    bulk_create_property_intel_records,
)

router = APIRouter(
    prefix="/heimdall/bulk-property",
    tags=["Heimdall Bulk Property Enrichment"],
)


class BulkPropertyRecord(BaseModel):
    address: Dict[str, Any]
    property_data: Dict[str, Any] = {}


class BulkPropertyEnrichmentRequest(BaseModel):
    records: List[BulkPropertyRecord]
    created_by: str = "heimdall"


@router.post("/enrich")
def bulk_enrich(
    payload: BulkPropertyEnrichmentRequest,
    db: Session = Depends(get_db),
):
    """
    Bulk create property intel records from driving-for-dollars list.
    
    Input: Array of property records
    
    Each record should contain:
    - address: {address, city, province_or_state, country}
      (address and city are required)
    - property_data: {visible_distress_observed, vacant_or_boarded, etc.}
      (optional, can be empty)
    
    Workflow:
    1. Validate each record (require address + city)
    2. Create property intel record
    3. System calculates research_status, distress_score, lead_lane
    4. Log any failures (invalid data, database errors)
    5. Return summary with created count, failed count, details
    
    Output:
    - created_count: Number of successfully created records
    - failed_count: Number of failed records
    - created: Array of created property records with IDs and scores
    - failed: Array of failures with reasons
    
    Use case:
    - Upload 50-100 driving-for-dollars addresses at once
    - Get bulk distress scores + lead lane assignments
    - Filter to HOT_LEAD properties
    - Start outreach orchestration
    
    Next step after this: CSV upload endpoint (upload spreadsheet, auto-parse)
    """
    return bulk_create_property_intel_records(
        db=db,
        records=[record.model_dump() for record in payload.records],
        created_by=payload.created_by,
    )
