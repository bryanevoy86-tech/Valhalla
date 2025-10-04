from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
import sqlalchemy as sa
from app.db import get_db  # adjust import to your project

router = APIRouter()
VALID = {"new","qualified","offer_sent","under_contract","closed","dead"}

@router.patch("/leads/{lead_id}/status")
def set_lead_status(lead_id: str, payload: dict, db: Session = Depends(get_db)):
    status = payload.get("status")
    if status not in VALID:
        raise HTTPException(400, "invalid status")
    lead = db.execute(sa.text("SELECT * FROM leads WHERE id=:id"), {"id": lead_id}).mappings().first()
    if not lead:
        raise HTTPException(404, "lead not found")
    now = datetime.now(timezone.utc)
    sla = None
    if status == "new": sla = now + timedelta(minutes=15)
    elif status == "qualified": sla = now + timedelta(hours=1)
    elif status == "offer_sent": sla = now + timedelta(hours=24)
    db.execute(
        sa.text("UPDATE leads SET status=:s, sla_expires_at=:sla WHERE id=:id"),
        {"s": status, "sla": sla, "id": lead_id},
    )
    db.commit()
    return {"ok": True, "status": status, "sla_expires_at": sla.isoformat() if sla else None}

@router.get("/slas/due")
def slas_due(db: Session = Depends(get_db)):
    rows = db.execute(sa.text("""
        SELECT id, status, sla_expires_at
        FROM leads
        WHERE sla_expires_at IS NOT NULL
          AND sla_expires_at < NOW()
          AND status NOT IN ('closed','dead')
        ORDER BY sla_expires_at ASC
        LIMIT 100
    """)).mappings().all()
    return {"count": len(rows), "items": rows}
