from __future__ import annotations
from typing import Any, Dict
from fastapi import APIRouter, Body
from . import store

router = APIRouter(prefix="/core/house_budget", tags=["core-house-budget"])

@router.get("")
def get_profile():
    return store.get_profile()

@router.post("")
def save(payload: Dict[str, Any] = Body(...)):
    return store.save_profile(payload or {})
