from __future__ import annotations

from fastapi import APIRouter, HTTPException
from . import service

router = APIRouter(prefix="/core/exports/year_end", tags=["core-exports-year-end"])


@router.post("")
def build(year: int, currency: str = "CAD"):
    try:
        return service.build(year=year, currency=currency)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("")
def list_items(limit: int = 10):
    return {"items": service.list_items(limit=limit)}
