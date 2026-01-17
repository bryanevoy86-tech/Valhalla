from __future__ import annotations

from fastapi import APIRouter, HTTPException
from . import service

router = APIRouter(prefix="/core/category_rules", tags=["core-category-rules"])

@router.post("")
def create(match_field: str, contains: str, category: str, priority: int = 100, notes: str = ""):
    try:
        return service.create(match_field=match_field, contains=contains, category=category, priority=priority, notes=notes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("")
def list_items(status: str = "active", q: str = ""):
    return {"items": service.list_items(status=status, q=q)}

@router.get("/apply_one")
def apply_one(merchant: str = "", description: str = ""):
    return {"category": service.apply_one(merchant=merchant, description=description)}
