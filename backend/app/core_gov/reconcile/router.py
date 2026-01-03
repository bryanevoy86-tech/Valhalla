from __future__ import annotations

from fastapi import APIRouter, HTTPException
from .schemas import ReconSuggestRequest, ReconSuggestResponse, ReconLinkCreate, ReconLinkRecord
from . import service

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
