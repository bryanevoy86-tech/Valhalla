from __future__ import annotations
from fastapi import APIRouter
from .service import run_for_deal
from .sent import mark_sent
from .daily import tick
from . import store

router = APIRouter(prefix="/core/pipeline", tags=["core-pipeline"])

@router.post("/deal/{deal_id}/run")
def run(deal_id: str, kind: str = "sms", tone: str = "neutral", to: str = "", create_followup_days: int = 2):
    return run_for_deal(deal_id=deal_id, kind=kind, tone=tone, to=to, create_followup_days=create_followup_days)

@router.get("/runs")
def runs(limit: int = 50):
    items = store.list_runs()
    items.sort(key=lambda x: x.get("created_at",""), reverse=True)
    return {"runs": items[:max(1, min(2000, int(limit or 50)))]}

@router.post("/runs/{run_id}/sent")
def sent(run_id: str, channel: str = "", result: str = "sent"):
    return mark_sent(run_id=run_id, channel=channel, result=result)

@router.post("/daily_tick")
def daily_tick(limit: int = 10):
    return tick(limit=limit)
