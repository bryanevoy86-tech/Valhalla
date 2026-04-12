"""Pack 59: Integrity + Telemetry - Service"""
import os, hmac, hashlib, json, datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.integrity.models import IntegrityEvent

def _get_prev_hash(db: Session):
    row = db.query(IntegrityEvent).order_by(IntegrityEvent.id.desc()).first()
    return row.event_hash if row else None

def _hmac(secret: str, message: str) -> str:
    return hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()

def record_integrity(db: Session, actor: str, action: str, scope: str, ref_id: str | None, payload_json: str | None):
    prev = _get_prev_hash(db)
    secret = os.getenv("INTEGRITY_HMAC_SECRET","change-me")
    base = json.dumps({"actor":actor,"action":action,"scope":scope,"ref_id":ref_id,"payload":payload_json or "","prev": prev or ""}, sort_keys=True)
    evhash = hashlib.sha256(base.encode()).hexdigest()
    sig = _hmac(secret, evhash)
    row = IntegrityEvent(actor=actor, action=action, scope=scope, ref_id=ref_id, payload_json=payload_json, prev_hash=prev, event_hash=evhash, sig=sig)
    db.add(row); db.commit(); db.refresh(row)
    return {"id": row.id, "hash": row.event_hash}

def verify_chain(db: Session, sample_last_n: int = 100):
    secret = os.getenv("INTEGRITY_HMAC_SECRET","change-me")
    rows = db.query(IntegrityEvent).order_by(IntegrityEvent.id.asc()).all()
    if not rows: return {"ok": True, "checked": 0}
    start = max(0, len(rows)-sample_last_n)
    prev = None
    for r in rows[start:]:
        base = json.dumps({"actor":r.actor,"action":r.action,"scope":r.scope,"ref_id":r.ref_id,"payload":r.payload_json or "","prev": prev or ""}, sort_keys=True)
        if hashlib.sha256(base.encode()).hexdigest() != r.event_hash:
            return {"ok": False, "at_id": r.id, "reason": "hash_mismatch"}
        if _hmac(secret, r.event_hash) != r.sig:
            return {"ok": False, "at_id": r.id, "reason": "sig_mismatch"}
        prev = r.event_hash
    return {"ok": True, "checked": len(rows)-start}

def record_telemetry(db: Session, category: str, name: str, latency_ms: int | None, ok: bool, dim: str | None):
    """Legacy telemetry function - telemetry system has been replaced with integrity tracking"""
    return {"status": "skipped", "reason": "telemetry_deprecated"}

def _rollup(db: Session, ev):
    """Legacy rollup function - no longer used"""
    pass
    db.commit()
