from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import sqlalchemy as sa
from datetime import datetime, timezone
from app.db import get_db

router = APIRouter()

@router.post("/agreements")
def create_agreement(payload: dict, db: Session = Depends(get_db)):
    p = {**payload, "created_at": datetime.now(timezone.utc)}
    db.execute(sa.text("""
        INSERT INTO agreements (lead_id, buyer_id, doc_url, created_at)
        VALUES (:lead_id, :buyer_id, :doc_url, :created_at)
    """), p)
    db.commit()
    return {"ok": True}
