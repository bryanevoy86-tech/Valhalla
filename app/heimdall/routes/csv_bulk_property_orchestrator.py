"""
CSV Bulk Property Enrichment Orchestrator Route
Prefix: /heimdall/csv-bulk-property
"""

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.heimdall.services.csv_bulk_property_orchestrator import (
    run_csv_bulk_property_enrichment,
)

router = APIRouter(
    prefix="/heimdall/csv-bulk-property",
    tags=["Heimdall CSV Bulk Property"],
)


@router.post("/upload")
async def upload_csv_bulk_property(
    file: UploadFile = File(...),
    created_by: str = Form("heimdall"),
    db: Session = Depends(get_db),
):
    """
    Upload CSV file → parse → batch create property intel records.

    **Workflow:**
    1. Validate .csv file extension
    2. Decode file as UTF-8-sig (handles BOM)
    3. Parse rows: validate required fields (address, city)
    4. Reject invalid rows, collect error details
    5. Batch create all valid records in property_intel database
    6. Return parse results + creation summary

    **CSV Expected Format:**
    Required: address, city
    Optional: province_or_state, country, visible_distress_observed, vacant_or_boarded, 
              ownership_unverified, notes, photo_url, estimated_arv, property_condition

    **Response:**
    {
        "status": "CSV_BULK_PROPERTY_ENRICHMENT_COMPLETE",
        "parsed": {
            "parsed_count": 5,
            "failed_count": 1,
            "failed": [{"row": 3, "reason": "missing address"}]
        },
        "created": {
            "created_count": 5,
            "failed_count": 0,
            "created": [{id, address, city, distress_score, research_status, ...}],
            "failed": []
        }
    }
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")

    content = await file.read()
    csv_text = content.decode("utf-8-sig")

    return run_csv_bulk_property_enrichment(
        db=db,
        csv_text=csv_text,
        created_by=created_by,
    )
