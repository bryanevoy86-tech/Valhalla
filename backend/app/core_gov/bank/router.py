from __future__ import annotations

from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException

from .schemas import BankTxnCreate, BankTxnListResponse
from . import service

router = APIRouter(prefix="/core/bank", tags=["core-bank"])


@router.post("/txns")
def create(payload: BankTxnCreate):
    try:
        return service.create(payload.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/txns", response_model=BankTxnListResponse)
def list_txns(status: str = "", account: str = "", q: str = "", limit: int = 200):
    return {"items": service.list_txns(status=status, account=account, q=q, limit=limit)}


@router.get("/txns/{txn_id}")
def get_one(txn_id: str):
    x = service.get_one(txn_id)
    if not x:
        raise HTTPException(status_code=404, detail="txn not found")
    return x


@router.patch("/txns/{txn_id}")
def patch(txn_id: str, patch: Dict[str, Any]):
    try:
        return service.patch(txn_id, patch)
    except KeyError:
        raise HTTPException(status_code=404, detail="txn not found")


@router.post("/txns/bulk_import")
def bulk_import(payloads: List[Dict[str, Any]], dedupe_external_id: bool = True, max_items: int = 500):
    return service.bulk_import(payloads, dedupe_external_id=dedupe_external_id, max_items=max_items)
