from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import sqlalchemy as sa
from app.core.settings import settings
from app.db import get_db

router = APIRouter()

@router.get("/features")
def get_features(db: Session = Depends(get_db)):
    rows = db.execute(sa.text("SELECT key, enabled FROM feature_flags")).all()
    db_flags = {k: e for k, e in rows} if rows else {}
    merged = {**settings.feature_flags, **db_flags}
    return merged
