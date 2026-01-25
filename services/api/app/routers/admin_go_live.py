from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.db import get_db
from app.models.system_metadata import SystemMetadata

router = APIRouter(prefix="/admin", tags=["admin"])

@router.post("/backend-complete")
def set_backend_complete(db: Session = Depends(get_db)):
    row = db.get(SystemMetadata, 1)
    if not row:
        row = SystemMetadata(id=1, version="1.0.0")
        db.add(row)
        db.flush()

    row.backend_complete = True
    row.completed_at = datetime.utcnow()
    row.updated_at = datetime.utcnow()
    db.commit()
    return {"ok": True, "backend_complete": row.backend_complete}
