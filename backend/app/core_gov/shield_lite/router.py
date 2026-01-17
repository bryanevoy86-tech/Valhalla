from __future__ import annotations
from fastapi import APIRouter, HTTPException
from typing import Any, Dict
from . import store
from .service import activate, deactivate
from .auto import check_and_trigger

router = APIRouter(prefix="/core/shield_lite", tags=["core-shield-lite"])

@router.get("")
def get():
    return store.get_state()

@router.post("/activate")
def activate_ep(reason: str = "risk", notes: str = ""):
    out = activate(reason=reason, notes=notes)
    if not out.get("ok"):
        raise HTTPException(status_code=400, detail=out.get("error"))
    return out

@router.post("/deactivate")
def deactivate_ep(notes: str = ""):
    return deactivate(notes=notes)

@router.post("/auto_check")
def auto_check(buffer_min: float = 500.0):
    return check_and_trigger(buffer_min=buffer_min)
