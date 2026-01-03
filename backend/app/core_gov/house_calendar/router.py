from __future__ import annotations

from fastapi import APIRouter, HTTPException
from . import service

router = APIRouter(prefix="/core/house_calendar", tags=["core-house-calendar"])

@router.post("")
def create(title: str, date: str, time: str = "", location: str = "", category: str = "household", notes: str = ""):
    try:
        return service.create(title=title, date=date, time=time, location=location, category=category, notes=notes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("")
def list_items(date_from: str = "", date_to: str = "", category: str = "", q: str = ""):
    return {"items": service.list_items(date_from=date_from, date_to=date_to, category=category, q=q)}
