from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.market_policy import MarketPolicy
from app.schemas.market_policy import MarketPolicyUpsertIn, MarketPolicyOut
from app.services.market_policy import upsert_policy, get_effective_policy, is_contact_allowed

router = APIRouter(prefix="/governance/market", tags=["Governance", "Market Policy"])


@router.get("/policies", response_model=list[MarketPolicyOut])
def list_policies(db: Session = Depends(get_db)):
    return db.query(MarketPolicy).order_by(MarketPolicy.province.asc(), MarketPolicy.market.asc()).all()


@router.post("/policies/upsert", response_model=MarketPolicyOut)
def upsert(body: MarketPolicyUpsertIn, db: Session = Depends(get_db)):
    return upsert_policy(db, body.province, body.market, body.enabled, body.rules, body.changed_by, body.reason)


@router.get("/effective")
def effective(province: str, market: str | None = None, db: Session = Depends(get_db)):
    row, rules = get_effective_policy(db, province, market)
    return {"found": bool(row), "province": province.upper(), "market": (market or "ALL").upper(), "rules": rules}


@router.get("/can-contact")
def can_contact(province: str, market: str | None, weekday: int, hhmm: str, channel: str, db: Session = Depends(get_db)):
    _, rules = get_effective_policy(db, province, market)
    ok, reason = is_contact_allowed(rules, weekday, hhmm, channel)
    return {"ok": ok, "reason": reason, "province": province.upper(), "market": (market or "ALL").upper(), "channel": channel.upper()}
