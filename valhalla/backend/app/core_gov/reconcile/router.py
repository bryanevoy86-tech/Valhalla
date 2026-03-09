from __future__ import annotations

from fastapi import APIRouter, HTTPException
from .schemas import ReconSuggestRequest, ReconSuggestResponse, ReconLinkCreate, ReconLinkRecord
from . import service, auto_accept, batch
from .alerts import push_missing_alerts

router = APIRouter(prefix="/core/reconcile", tags=["core-reconcile"])


@router.post("/suggest", response_model=ReconSuggestResponse)
def suggest(payload: ReconSuggestRequest):
    return service.suggest(
        bank_txn_id=payload.bank_txn_id,
        max_suggestions=payload.max_suggestions,
        amount_tolerance=payload.amount_tolerance,
        days_tolerance=payload.days_tolerance,
    )


@router.post("/link", response_model=ReconLinkRecord)
def link(payload: ReconLinkCreate):
    try:
        return service.link(
            bank_txn_id=payload.bank_txn_id,
            target_type=payload.target_type,
            target_id=payload.target_id,
            note=payload.note,
            meta=payload.meta,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/links")
def links(bank_txn_id: str = ""):
    return {"items": service.list_links(bank_txn_id=bank_txn_id)}


@router.post("/auto_accept")
def auto_accept_link(bank_txn_id: str, threshold: float = 0.92, amount_tolerance: float = 1.0, days_tolerance: int = 5):
    return auto_accept.auto_accept(bank_txn_id=bank_txn_id, threshold=threshold, amount_tolerance=amount_tolerance, days_tolerance=days_tolerance)


@router.post("/batch_run")
def batch_run(limit: int = 200, threshold: float = 0.92):
    return batch.run_batch(limit=limit, threshold=threshold)


@router.get("/payments")
def reconcile_payments(days: int = 30):
    out = service.reconcile(days=days)
    if not out.get("ok"):
        raise HTTPException(status_code=503, detail=out.get("error"))
    return out


@router.post("/payments/push_alerts")
def push_alerts(days: int = 30):
    out = service.reconcile(days=days)
    if not out.get("ok"):
        raise HTTPException(status_code=503, detail=out.get("error"))
    return push_missing_alerts(out.get("missing") or [])
