from __future__ import annotations
from fastapi import APIRouter, HTTPException
from typing import Any, Dict
from .service import log_usage, forecast_days_left
from .rollup import rollup

router = APIRouter(prefix="/core/forecast", tags=["core-forecast"])

@router.post("/usage")
def usage(inv_id: str, qty_used: float, used_on: str = "", notes: str = ""):
    if not inv_id:
        raise HTTPException(status_code=400, detail="inv_id required")
    return log_usage(inv_id=inv_id, qty_used=qty_used, used_on=used_on, notes=notes)

@router.get("/inventory/{inv_id}")
def inv_forecast(inv_id: str, window_days: int = 30):
    try:
        from backend.app.core_gov.inventory import store as istore  # type: ignore
        items = istore.list_items()
        it = next((x for x in items if x.get("id") == inv_id), None)
    except Exception:
        it = None
    if not it:
        raise HTTPException(status_code=404, detail="inventory item not found")
    return forecast_days_left(inv_item=it, window_days=window_days)

@router.get("/rollup")
def rollup_ep(limit: int = 20, window_days: int = 30):
    return rollup(limit=limit, window_days=window_days)
