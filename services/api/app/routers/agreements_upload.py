from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
import sqlalchemy as sa
from app.db import get_db

router = APIRouter()

@router.post("/agreements/{agreement_id}/upload")
def upload_signed_doc(agreement_id: str, payload: dict, db: Session = Depends(get_db)):
    url = payload.get("signed_doc_url")
    if not url:
        raise HTTPException(400, "Missing signed_doc_url")
    db.execute(sa.text("UPDATE agreements SET doc_url=:url WHERE id=:id"), {"url": url, "id": agreement_id})
    db.commit()
    return {"ok": True, "doc_url": url}
