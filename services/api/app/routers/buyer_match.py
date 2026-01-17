from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

router = APIRouter(prefix="/buyer", tags=["buyer"])

class BuyerIn(BaseModel):
    email: str
    name: str
    phone: Optional[str] = None

class PrefsIn(BaseModel):
    regions: List[str]
    asset_types: List[str]
    min_arv: float
    max_arv: float
    min_bed: int = 0
    min_bath: float = 0.0
    max_repair_cost: float = 999999
    yield_target_pct: float = 0.0
    notes: Optional[str] = None

@router.post("/upsert")
def upsert_buyer(payload: BuyerIn):
    return {"ok": True, "buyer_id": 7001}

@router.post("/{buyer_id}/prefs")
def set_prefs(buyer_id: int, prefs: PrefsIn):
    return {"ok": True}

@router.get("/match/{deal_id}")
def match_buyers(deal_id: int, min_score: int = 60, limit: int = 25):
    return {"deal_id": deal_id, "matches": [{"buyer_id":7001,"score":88}]}

@router.post("/notify/{deal_id}")
def notify_matches(deal_id: int, min_score: int = 70):
    return {"ok": True, "notified": 12}

@router.post("/claim")
def claim_deal(deal_id: int, buyer_id: int):
    return {"ok": True, "status": "claimed", "ttl_min": 60}

@router.post("/assign")
def assign_buyer(deal_id: int, buyer_id: int):
    return {"ok": True, "status": "assigned"}
