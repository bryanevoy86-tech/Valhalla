from fastapi import APIRouter, UploadFile, File, HTTPException

from app.heimdall.services.csv_property_parser_service import parse_property_csv

router = APIRouter(
    prefix="/heimdall/csv-property",
    tags=["Heimdall CSV Property Parser"],
)


@router.post("/parse")
async def parse_csv(file: UploadFile = File(...)):
    """
    Parse driving-for-dollars CSV and convert to bulk enrichment format.
    
    Input: CSV file upload
    
    Required columns: address, city
    
    Optional columns:
    - province_or_state (or province or state)
    - country (defaults to Canada)
    - visible_distress_observed (true/yes/1 converted to boolean)
    - vacant_or_boarded (true/yes/1 converted to boolean)
    - ownership_unverified (defaults to true)
    - notes (free text)
    - photo_url (URL to property photo)
    - estimated_arv (estimated after-repair value)
    - property_condition (unknown|poor|fair|good|excellent)
    - vacant_or_occupied (unknown|vacant|occupied)
    
    Output: Parsed records ready for bulk enrichment
    
    Workflow:
    1. Upload CSV file (address,city,province_or_state,visible_distress_observed,...)
    2. System parses + validates (require address + city)
    3. Converts boolean strings (true/yes/1) to boolean
    4. Returns parsed records + failures
    5. Take parsed records → POST /bulk-property/enrich
    
    Example CSV:
    address,city,province_or_state,country,visible_distress_observed,vacant_or_boarded,notes
    123 Main St,Winnipeg,Manitoba,Canada,yes,no,Boarded windows
    456 Oak Ave,Brandon,Manitoba,Canada,true,true,Vacant 2 years
    
    Use case:
    - Export from Google Maps, driving-for-dollars app, or spreadsheet
    - Upload CSV here
    - Get back parsed records (with validation errors)
    - Fix errors, re-upload if needed
    - Take clean records → POST /bulk-property/enrich to create property intel
    """

    # Validate file type
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=400, detail="Only CSV files are supported."
        )

    # Read and decode file
    content = await file.read()
    csv_text = content.decode("utf-8-sig")

    # Parse CSV
    return parse_property_csv(csv_text)
