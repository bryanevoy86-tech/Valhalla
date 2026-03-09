import time

from sqlalchemy.orm import Session

from ..core.db import SessionLocal
from ..models.lead import Lead


def enrich_lead_task(lead_id: int):
    """
    Fake long-running enrichment: sleep, then append a note to the lead's notes field.
    Replace with real enrichment (skip tracing, skip network here).
    """
    time.sleep(3)
    db: Session = SessionLocal()
    try:
        obj = db.query(Lead).get(lead_id)
        if not obj:
            return {"ok": False, "reason": "lead not found"}
        obj.notes = (obj.notes or "") + "\n[auto] Enriched basics."
        db.add(obj)
        db.commit()
        return {"ok": True, "lead_id": lead_id}
    finally:
        db.close()
