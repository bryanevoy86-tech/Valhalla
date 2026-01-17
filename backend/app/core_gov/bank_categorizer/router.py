from __future__ import annotations

from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException
from . import service

router = APIRouter(prefix="/core/bank_categorizer", tags=["core-bank-categorizer"])


@router.post("/rules")
def create_rule(name: str, contains: str, category: str, tags_add: List[str] = None, confidence: float = 0.8, status: str = "active"):
    try:
        return service.create_rule(name=name, contains=contains, category=category, tags_add=tags_add, confidence=confidence, status=status)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/rules")
def list_rules(status: str = ""):
    return {"items": service.list_rules(status=status)}


@router.post("/apply")
def apply(bank_txn_id: str, create_receipt: bool = False):
    return service.apply_to_bank_txn(bank_txn_id=bank_txn_id, create_receipt=create_receipt)
