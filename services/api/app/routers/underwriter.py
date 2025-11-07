"""Pack 62: Underwriter Router (stub)"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from decimal import Decimal

router = APIRouter(prefix="/underwriter", tags=["underwriter"])

class DealIn(BaseModel):
    address: str
    city: str
    province: str
    postal_code: Optional[str] = None
    ask_price: Decimal
    bed: Optional[int] = None
    bath: Optional[float] = None
    sqft: Optional[int] = None
    notes: Optional[str] = None
    meta: Dict[str, Any] = {}

class CompIn(BaseModel):
    address: str
    sold_price: Decimal
    sold_ts: Optional[str] = None
    bed: Optional[int] = None
    bath: Optional[float] = None
    sqft: Optional[int] = None
    distance_km: float = 0.5
    adj_factor: float = 1.0

class ScreenResult(BaseModel):
    arv: float
    repair_cost: float
    roi_pct: float
    ltv_pct: float
    dti_pct: float
    score: float
    recommendation: str
    summary: str

@router.post("/deal")
def create_deal(payload: DealIn):
    return {"deal_id": 1001, "status": "new"}

@router.post("/deal/{deal_id}/comps")
def add_comps(deal_id: int, comps: List[CompIn]):
    return {"ok": True, "count": len(comps)}

@router.post("/deal/{deal_id}/screen", response_model=ScreenResult)
def screen_deal(deal_id: int, cap_rate_hint: Optional[float] = Query(None)):
    return ScreenResult(
        arv=325000.0, repair_cost=42000.0, roi_pct=22.5, ltv_pct=68.0, dti_pct=37.0,
        score=86.0, recommendation="offer",
        summary="Solid spread; ROI above target; LTV within policy."
    )

@router.get("/deal/{deal_id}/score")
def deal_score(deal_id: int):
    return {"deal_id": deal_id, "score": 86.0, "recommendation": "offer"}
