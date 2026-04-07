from __future__ import annotations

import json
from datetime import datetime
from typing import Dict, Any, Tuple

from sqlalchemy.orm import Session

from app.models.offer_policy import OfferPolicy
from app.models.offer_evidence import OfferEvidence
from app.services.kpi import emit_kpi


def _get_policy(db: Session, province: str, market: str) -> OfferPolicy:
    province = province.strip().upper()
    market = (market or "ALL").strip().upper()

    row = db.query(OfferPolicy).filter(OfferPolicy.province == province, OfferPolicy.market == market).first()
    if not row:
        row = db.query(OfferPolicy).filter(OfferPolicy.province == province, OfferPolicy.market == "ALL").first()
    if not row:
        # Safe default: disabled until configured
        row = OfferPolicy(province=province, market="ALL", enabled=False)
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def compute_offer(db: Session, province: str, market: str, arv: float, repairs: float, comps: Dict[str, Any] | None, assumptions: Dict[str, Any] | None, correlation_id: str | None) -> Dict[str, Any]:
    pol = _get_policy(db, province, market)
    if not pol.enabled:
        raise RuntimeError("OfferPolicy disabled for this market")

    arv = float(arv)
    repairs = float(repairs)
    fees = float(pol.default_fees_buffer)

    mao = (arv * float(pol.max_arv_multiplier)) - repairs - fees
    recommended_offer = max(0.0, mao)

    ev = OfferEvidence(
        province=province.strip().upper(),
        market=(market or "ALL").strip().upper(),
        arv=arv,
        repairs=repairs,
        fees_buffer=fees,
        mao=mao,
        recommended_offer=recommended_offer,
        comps_json=json.dumps(comps) if comps else None,
        assumptions_json=json.dumps(assumptions) if assumptions else None,
        correlation_id=correlation_id,
        created_at=datetime.utcnow(),
    )
    db.add(ev)
    db.commit()
    db.refresh(ev)

    emit_kpi(db, "WHOLESALE", "offer_generated", success=True, correlation_id=correlation_id, detail={"evidence_id": ev.id, "province": ev.province, "market": ev.market})
    return {
        "policy": {"max_arv_multiplier": pol.max_arv_multiplier, "fees_buffer": pol.default_fees_buffer, "assignment_fee": pol.default_assignment_fee},
        "calc": {"arv": arv, "repairs": repairs, "fees_buffer": fees, "mao": mao, "recommended_offer": recommended_offer},
        "evidence_id": ev.id,
    }
