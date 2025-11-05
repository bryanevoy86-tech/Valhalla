from typing import List
from fastapi import APIRouter

from app.alerts.service import AlertsService
from app.alerts.schemas import AlertOut
from app.metrics.service import MetricsService


router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=List[AlertOut])
async def get_alerts():
    """
    Check current metrics against thresholds and return any active alerts.
    
    Returns a list of alerts (may be empty if no thresholds exceeded).
    """
    metrics = MetricsService.get_metrics()
    alerts = AlertsService.check_thresholds(metrics)
    return alerts
