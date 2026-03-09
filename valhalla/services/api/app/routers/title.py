from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import sqlalchemy as sa
from app.db import get_db

router = APIRouter()

@router.post("/title/orders")
def create_title_order(payload: dict, db: Session = Depends(get_db)):
    db.execute(sa.text("""
        INSERT INTO title_orders (lead_id, escrow_company, officer_name, file_number, created_at)
        VALUES (:lead_id, :escrow_company, :officer_name, :file_number, NOW())
    """), payload)
    db.commit()
    return {"ok": True}
