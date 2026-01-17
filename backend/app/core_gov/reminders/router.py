from __future__ import annotations

from typing import Any, Dict
from fastapi import APIRouter, HTTPException

from .schemas import (
    ReminderCreate, ReminderListResponse,
    GenerateFromBudgetRequest, GenerateFromShoppingRequest
)
from . import service

router = APIRouter(prefix="/core/reminders", tags=["core-reminders"])


@router.post("")
def create(payload: ReminderCreate):
    try:
        return service.create(payload.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=ReminderListResponse)
def list_items(status: str = "", source: str = ""):
    return {"items": service.list_items(status=status, source=source)}


@router.patch("/{reminder_id}")
def patch(reminder_id: str, patch: Dict[str, Any]):
    try:
        return service.patch(reminder_id, patch)
    except KeyError:
        raise HTTPException(status_code=404, detail="reminder not found")


@router.post("/generate/from_budget")
def gen_budget(payload: GenerateFromBudgetRequest):
    return service.generate_from_budget(
        lookahead_days=payload.lookahead_days,
        lead_days=payload.lead_days,
        max_create=payload.max_create,
    )


@router.post("/generate/from_shopping")
def gen_shopping(payload: GenerateFromShoppingRequest):
    return service.generate_from_shopping(
        default_lead_days=payload.default_lead_days,
        max_create=payload.max_create,
    )
