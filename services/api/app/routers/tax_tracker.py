"""Pack 60: Tax Tracker Router (stub)"""
from fastapi import APIRouter, UploadFile, File, Query
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from decimal import Decimal

router = APIRouter(prefix="/tax", tags=["tax"])

class ItemIn(BaseModel):
    description: str
    qty: float = 1.0
    unit_price: Decimal
    category_code: Optional[str] = None
    business_use_pct: float = 100.0
    notes: Optional[str] = None

class ReceiptIn(BaseModel):
    vendor: str
    total: Decimal
    tax_paid: Decimal = Decimal("0.00")
    currency: str = "CAD"
    items: List[ItemIn] = []
    meta: Dict[str, Any] = {}

@router.post("/receipt/upload")
async def upload_receipt(file: UploadFile = File(...)):
    return {"ok": True, "image_url": "s3://valhalla-receipts/demo.jpg", "status": "uploaded"}

@router.post("/receipt")
async def create_receipt(payload: ReceiptIn):
    return {"ok": True, "receipt_id": 123}

@router.get("/receipt/{receipt_id}")
async def get_receipt(receipt_id: int):
    return {"id": receipt_id, "status": "categorized", "risk": 0.18}

@router.post("/categorize/{receipt_id}")
async def categorize(receipt_id: int):
    return {"ok": True}

@router.get("/writeoff/suggest")
async def suggest_writeoffs(month: str = Query(..., example="2025-11"), jurisdiction: str = "CAN"):
    return {"month": month, "jurisdiction": jurisdiction, "suggestions": []}

@router.get("/export/bundle")
async def export_bundle(year: int = 2025, jurisdiction: str = "CAN", format: str = "zip"):
    return {"url": f"s3://valhalla-exports/CRA-{year}.zip", "expires_days": 30}

@router.get("/risk/meter")
async def risk_meter():
    return {"low": 0.72, "med": 0.22, "high": 0.06, "top_flags": ["vehicle_pct_high","missing_contracts"]}
