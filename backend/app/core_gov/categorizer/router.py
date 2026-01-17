from __future__ import annotations

from fastapi import APIRouter, HTTPException
from .schemas import (
    CategoryRuleCreate, RuleListResponse,
    CategorizeReceiptRequest, CategorizeReceiptResponse
)
from . import service

router = APIRouter(prefix="/core/categorizer", tags=["core-categorizer"])


@router.post("/rules")
def create_rule(payload: CategoryRuleCreate):
    try:
        return service.create_rule(payload.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/rules", response_model=RuleListResponse)
def rules(status: str = ""):
    return {"items": service.list_rules(status=status)}


@router.post("/categorize_receipt", response_model=CategorizeReceiptResponse)
def categorize(payload: CategorizeReceiptRequest):
    return service.categorize_receipt(receipt_id=payload.receipt_id, apply=payload.apply, meta=payload.meta)
