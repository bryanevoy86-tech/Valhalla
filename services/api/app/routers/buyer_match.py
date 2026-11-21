"""Private buyer preferences, matching and internal deal reservations."""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr, model_validator
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.dependencies import require_prime_control_key
from app.models.buyer_candidate import BuyerCandidate
from app.models.deal_buyer_match import DealBuyerMatch
from app.models.match import DealBrief

router = APIRouter(prefix="/buyer", tags=["buyer"], dependencies=[Depends(require_prime_control_key)])
CLAIM_TTL_MIN = 60


class BuyerIn(BaseModel):
    email: EmailStr
    name: str
    phone: str | None = None


class PrefsIn(BaseModel):
    regions: list[str]
    asset_types: list[str]
    min_arv: float
    max_arv: float
    min_bed: int = 0
    min_bath: float = 0.0
    max_repair_cost: float = 999999
    yield_target_pct: float = 0.0
    notes: str | None = None

    @model_validator(mode="after")
    def check_ranges(self):
        if self.min_arv < 0 or self.max_arv < self.min_arv or min(self.min_bed, self.min_bath, self.max_repair_cost) < 0:
            raise ValueError("Invalid buyer preference ranges")
        return self


def _get_buyer(db: Session, buyer_id: int) -> BuyerCandidate:
    buyer = db.get(BuyerCandidate, buyer_id)
    if buyer is None:
        raise HTTPException(status_code=404, detail="Buyer not found")
    return buyer


def _brief(db: Session, deal_id: int, *, lock: bool = False) -> DealBrief:
    brief = db.get(DealBrief, deal_id, with_for_update=lock)
    if brief is None:
        raise HTTPException(status_code=404, detail="Deal brief not found")
    return brief


@router.post("/upsert")
def upsert_buyer(payload: BuyerIn, db: Session = Depends(get_db)):
    email = str(payload.email).strip().lower()
    buyer = db.query(BuyerCandidate).filter(func.lower(BuyerCandidate.email) == email).with_for_update().first()
    if buyer is None:
        buyer = BuyerCandidate(email=email, name=payload.name, phone=payload.phone)
        db.add(buyer)
    else:
        buyer.name = payload.name
        if payload.phone is not None:
            buyer.phone = payload.phone
    db.commit()
    return {"ok": True, "buyer_id": buyer.id}


@router.post("/{buyer_id}/prefs")
def set_prefs(buyer_id: int, prefs: PrefsIn, db: Session = Depends(get_db)):
    buyer = _get_buyer(db, buyer_id)
    buyer.buy_box = prefs.model_dump_json()
    db.commit()
    return {"ok": True}


def _score(brief: DealBrief, prefs: PrefsIn) -> int:
    regions = {value.strip().casefold() for value in prefs.regions}
    assets = {value.strip().casefold() for value in prefs.asset_types}
    facts = (
        (not regions or (brief.region or "").casefold() in regions, 30),
        (not assets or (brief.property_type or "").casefold() in assets, 25),
        (brief.arv is not None and prefs.min_arv <= float(brief.arv) <= prefs.max_arv, 20),
        (prefs.min_bed <= (brief.beds or 0) and prefs.min_bath <= (brief.baths or 0), 10),
        (brief.rehab_estimate is not None and float(brief.rehab_estimate) <= prefs.max_repair_cost, 10),
    )
    if prefs.yield_target_pct > 0:
        if brief.monthly_cashflow_estimate is None or not brief.price or brief.price <= 0:
            return 0
        if float(brief.monthly_cashflow_estimate / brief.price) * 1200 < prefs.yield_target_pct:
            return 0
    return sum(weight for matched, weight in facts if matched) + 5


@router.get("/match/{deal_id}")
def match_buyers(
    deal_id: int, min_score: int = Query(60, ge=0, le=100),
    limit: int = Query(25, ge=1, le=200), db: Session = Depends(get_db),
):
    brief = _brief(db, deal_id)
    matches = []
    for buyer in db.query(BuyerCandidate).filter(BuyerCandidate.buy_box.is_not(None)):
        try:
            prefs = PrefsIn.model_validate_json(buyer.buy_box)
        except ValueError:
            continue
        score = _score(brief, prefs)
        if score >= min_score:
            matches.append({"buyer_id": buyer.id, "score": score})
    matches.sort(key=lambda item: (-item["score"], item["buyer_id"]))
    return {"deal_id": deal_id, "matches": matches[:limit]}


@router.post("/notify/{deal_id}")
def notify_matches(deal_id: int, min_score: int = Query(70, ge=0, le=100), db: Session = Depends(get_db)):
    return {**match_buyers(deal_id, min_score, 25, db), "notified": 0, "status": "preview"}


def _reservation(db: Session, deal_id: int, buyer_id: int, *, assign: bool) -> DealBuyerMatch:
    _brief(db, deal_id, lock=True)
    _get_buyer(db, buyer_id)
    now = datetime.utcnow()
    matches = db.query(DealBuyerMatch).filter_by(deal_id=deal_id).order_by(DealBuyerMatch.id).all()
    current = next((item for item in matches if item.buyer_id == buyer_id), None)
    for item in matches:
        active_claim = item.match_status == "claimed" and item.claim_expires_at and item.claim_expires_at > now
        if item.buyer_id != buyer_id and (item.match_status == "assigned" or active_claim):
            raise HTTPException(status_code=409, detail="Deal already reserved for a different buyer")
    if current is None:
        current = DealBuyerMatch(deal_id=deal_id, buyer_id=buyer_id)
        db.add(current)
    if assign:
        if current.match_status != "assigned" and (
            current.match_status != "claimed" or current.claim_expires_at is None or current.claim_expires_at <= now
        ):
            raise HTTPException(status_code=409, detail="An active buyer claim is required before assignment")
        current.match_status, current.claim_expires_at = "assigned", None
    elif current.match_status != "assigned":
        current.match_status, current.claim_expires_at = "claimed", now + timedelta(minutes=CLAIM_TTL_MIN)
    db.commit()
    return current


@router.post("/claim")
def claim_deal(deal_id: int, buyer_id: int, db: Session = Depends(get_db)):
    row = _reservation(db, deal_id, buyer_id, assign=False)
    return {"ok": True, "status": row.match_status, "ttl_min": CLAIM_TTL_MIN if row.claim_expires_at else None}


@router.post("/assign")
def assign_buyer(deal_id: int, buyer_id: int, db: Session = Depends(get_db)):
    row = _reservation(db, deal_id, buyer_id, assign=True)
    return {"ok": True, "status": row.match_status}
