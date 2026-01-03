from __future__ import annotations

from fastapi import APIRouter
from . import service

router = APIRouter(prefix="/core/finance_alerts", tags=["core-finance-alerts"])


@router.post("/run")
def run(unreconciled_threshold: int = 25):
    return service.run_checks(unreconciled_threshold=unreconciled_threshold)
