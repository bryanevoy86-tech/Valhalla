from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
import sqlalchemy as sa
from app.db import get_db

router = APIRouter()

@router.post("/exports/{job_id}/upload")
def upload_export_url(job_id: str, payload: dict, db: Session = Depends(get_db)):
    url = payload.get("export_url")
    if not url:
        raise HTTPException(400, "Missing export_url")
    db.execute(sa.text("UPDATE export_jobs SET export_url=:url WHERE id=:id"), {"url": url, "id": job_id})
    db.commit()
    return {"ok": True, "export_url": url}
