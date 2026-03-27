from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, HTTPException

from .schemas import TransactionCreate, TransactionListResponse
from . import service

router = APIRouter(prefix="/core/transactions", tags=["core-transactions"])


@router.post("")
def create(payload: TransactionCreate):
    try:
        return service.create_tx(payload.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=TransactionListResponse)
def list_all(
    tx_type: Optional[str] = None,
    status: Optional[str] = None,
    bucket_id: Optional[str] = None,
    month: Optional[str] = None,
):
    return {"items": service.list_txs(tx_type=tx_type, status=status, bucket_id=bucket_id, month=month)}


@router.post("/{tx_id}/void")
def void(tx_id: str):
    try:
        return service.void_tx(tx_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="transaction not found")
