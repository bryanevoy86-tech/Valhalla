from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..core.db import get_db

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.post("")
async def create_metric(data: dict, db: Session = Depends(get_db)):
    return {"ok": True, "message": "Metric created"}


@router.get("")
async def list_metrics(db: Session = Depends(get_db)):
    return {"metrics": []}
