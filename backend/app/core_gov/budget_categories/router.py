from __future__ import annotations
from fastapi import APIRouter, HTTPException
from . import store

router = APIRouter(prefix="/core/budget/categories", tags=["core-budget-categories"])

@router.get("")
def list_items():
    return {"items": store.list_items()}

@router.post("")
def add(name: str):
    try:
        return {"items": store.add(name)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
