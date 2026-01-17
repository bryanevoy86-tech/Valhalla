from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.kpi_metric import KpiMetric
from app.schemas.kpi import KpiMetricCreate, KpiMetricUpdate, KpiMetricOut

router = APIRouter()


@router.post("/", response_model=KpiMetricOut)
def create_kpi_metric(
    payload: KpiMetricCreate,
    db: Session = Depends(get_db),
):
    obj = KpiMetric(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/", response_model=list[KpiMetricOut])
def list_kpi_metrics(
    name: str | None = None,
    scope: str | None = None,
    scope_ref: str | None = None,
    period: str | None = None,
    period_label: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(KpiMetric)
    if name:
        query = query.filter(KpiMetric.name == name)
    if scope:
        query = query.filter(KpiMetric.scope == scope)
    if scope_ref:
        query = query.filter(KpiMetric.scope_ref == scope_ref)
    if period:
        query = query.filter(KpiMetric.period == period)
    if period_label:
        query = query.filter(KpiMetric.period_label == period_label)
    return query.all()


@router.put("/{metric_id}", response_model=KpiMetricOut)
def update_kpi_metric(
    metric_id: int,
    payload: KpiMetricUpdate,
    db: Session = Depends(get_db),
):
    obj = db.query(KpiMetric).get(metric_id)
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj
