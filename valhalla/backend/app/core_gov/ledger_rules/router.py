from __future__ import annotations
from fastapi import APIRouter, HTTPException
from . import service

router = APIRouter(prefix="/core/ledger_rules", tags=["core-ledger-rules"])

@router.post("")
def create(pattern: str, category: str):
    try:
        return service.create(pattern=pattern, category=category)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/apply")
def apply(description: str):
    return {"category": service.apply(description=description)}
