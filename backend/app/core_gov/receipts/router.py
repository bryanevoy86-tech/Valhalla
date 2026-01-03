from __future__ import annotations

from typing import Any, Dict
from fastapi import APIRouter, HTTPException

from .schemas import ReceiptCreate, ReceiptListResponse
from . import service

router = APIRouter(prefix="/core/receipts", tags=["core-receipts"])


@router.post("")
def create(payload: ReceiptCreate):
    try:
        return service.create(payload.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=ReceiptListResponse)
def list_items(status: str = "", category: str = "", vendor: str = "", tag: str = ""):
    return {"items": service.list_items(status=status, category=category, vendor=vendor, tag=tag)}


@router.get("/{receipt_id}")
def get_one(receipt_id: str):
    x = service.get_one(receipt_id)
    if not x:
        raise HTTPException(status_code=404, detail="receipt not found")
    return x


@router.patch("/{receipt_id}")
def patch(receipt_id: str, patch: Dict[str, Any]):
    try:
        return service.patch(receipt_id, patch)
    except KeyError:
        raise HTTPException(status_code=404, detail="receipt not found")

@router.post("/{receipt_id}/post_ledger")
def post_ledger(receipt_id: str, account_id: str = ""):
    try:
        from .post_to_ledger import post as post_to_ledger
        return post_to_ledger(receipt_id=receipt_id, account_id=account_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="not found")
