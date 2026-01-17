from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.offer_policy import OfferPolicy
from app.services.offer_strategy import compute_offer

from app.core.execution_class import set_exec_class, ExecClass

router = APIRouter(prefix="/deals/offers", tags=["Deals", "Offer Strategy"])


@router.get("/policies")
def list_policies(db: Session = Depends(get_db)):
    rows = db.query(OfferPolicy).order_by(OfferPolicy.province.asc(), OfferPolicy.market.asc()).all()
    return {"ok": True, "policies": [{
        "province": r.province, "market": r.market, "enabled": r.enabled,
        "max_arv_multiplier": r.max_arv_multiplier, "default_assignment_fee": r.default_assignment_fee,
        "default_fees_buffer": r.default_fees_buffer, "updated_at": r.updated_at
    } for r in rows]}


@router.post("/policies/upsert")
def upsert_policy(province: str, market: str = "ALL", enabled: bool = True,
                  max_arv_multiplier: float = 0.70, default_assignment_fee: float = 10000.0, default_fees_buffer: float = 2500.0,
                  changed_by: str = "bryan", reason: str | None = None,
                  db: Session = Depends(get_db)):
    province = province.strip().upper()
    market = (market or "ALL").strip().upper()

    row = db.query(OfferPolicy).filter(OfferPolicy.province == province, OfferPolicy.market == market).first()
    if not row:
        row = OfferPolicy(province=province, market=market)
        db.add(row)

    row.enabled = bool(enabled)
    row.max_arv_multiplier = float(max_arv_multiplier)
    row.default_assignment_fee = float(default_assignment_fee)
    row.default_fees_buffer = float(default_fees_buffer)
    row.changed_by = changed_by
    row.reason = reason
    db.commit()
    db.refresh(row)
    return {"ok": True}


@router.post("/compute")
@set_exec_class(ExecClass.SANDBOX_EXEC)
def compute(province: str, market: str = "ALL", arv: float = 0.0, repairs: float = 0.0,
            comps_json: str | None = None, assumptions_json: str | None = None,
            correlation_id: str | None = None,
            db: Session = Depends(get_db)):
    import json
    comps = json.loads(comps_json) if comps_json else None
    assumptions = json.loads(assumptions_json) if assumptions_json else None
    out = compute_offer(db, province, market, arv, repairs, comps, assumptions, correlation_id)
    return {"ok": True, **out}
