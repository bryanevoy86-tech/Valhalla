from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse, JSONResponse

from app.core_gov.audit.audit_log import audit
from app.core_gov.deals.import_export import import_json, import_csv_text, export_json, export_csv, ALLOWED_SOURCES

router = APIRouter(prefix="/deals", tags=["Core: Deals"])

@router.post("/import/json")
def import_json_endpoint(payload: dict):
    items = payload.get("items")
    source = payload.get("lead_source")  # optional forced source

    if not isinstance(items, list):
        raise HTTPException(status_code=400, detail="payload.items must be a list")

    if source and source not in ALLOWED_SOURCES:
        raise HTTPException(status_code=400, detail=f"lead_source must be one of {sorted(ALLOWED_SOURCES)}")

    res = import_json(items, forced_source=source)
    audit("DEALS_IMPORTED_JSON", {"created": res["created"], "forced_source": source})
    return res

@router.post("/import/csv")
def import_csv_endpoint(payload: dict):
    csv_text = payload.get("csv")
    source = payload.get("lead_source")  # optional forced source

    if not csv_text or not isinstance(csv_text, str):
        raise HTTPException(status_code=400, detail="payload.csv must be a string")

    if source and source not in ALLOWED_SOURCES:
        raise HTTPException(status_code=400, detail=f"lead_source must be one of {sorted(ALLOWED_SOURCES)}")

    res = import_csv_text(csv_text, forced_source=source)
    audit("DEALS_IMPORTED_CSV", {"created": res["created"], "forced_source": source})
    return res

@router.get("/export/json")
def export_json_endpoint(limit: int = 5000):
    return {"items": export_json(limit=limit)}

@router.get("/export/csv")
def export_csv_endpoint(limit: int = 5000):
    text = export_csv(limit=limit)
    return PlainTextResponse(text, media_type="text/csv")
