from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..core.db import get_db
from ..models.metric import Metric
from ..schemas.metric import MetricIn, MetricOut

router = APIRouter(prefix="/metrics", tags=["metrics"])

@router.post("", response_model=MetricOut)
def create_metric(payload: MetricIn, db: Session = Depends(get_db)):
    m = Metric(name=payload.name, value=payload.value, unit=payload.unit, tags=payload.tags)
    db.add(m)
    db.commit()
    db.refresh(m)
    return m

@router.get("", response_model=List[MetricOut])
def list_metrics(
    name: Optional[str] = Query(default=None),
    tag_contains: Optional[str] = Query(default=None),
    limit: int = 100,
    db: Session = Depends(get_db)
):
    q = db.query(Metric)
    if name:
        q = q.filter(Metric.name == name)
    if tag_contains:
        q = q.filter(Metric.tags.ilike(f"%{tag_contains}%"))
    return q.order_by(Metric.id.desc()).limit(limit).all()
