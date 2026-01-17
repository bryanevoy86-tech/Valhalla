from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.metrics.runtime import metrics_store
from app.core.metrics.metrics_store import SystemMetrics

router = APIRouter(prefix="/api/metrics", tags=["metrics"])


class MetricsBody(BaseModel):
    monthly_net_cad: float | None = None
    monthly_burn_cad: float | None = None
    critical_runbook_blockers: int | None = None
    outcomes_required_ratio: float | None = None
    outcomes_recorded_ratio: float | None = None
    clean_promotion_enabled: bool | None = None


@router.get("")
def get_metrics():
    return metrics_store.load().__dict__


@router.post("")
def update_metrics(body: MetricsBody):
    try:
        m = metrics_store.load()
        for k, v in body.dict(exclude_none=True).items():
            setattr(m, k, v)
        metrics_store.save(m)
        return {"ok": True, "metrics": m.__dict__}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
