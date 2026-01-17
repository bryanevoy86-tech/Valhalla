from __future__ import annotations
from typing import Any, Dict
from fastapi import APIRouter, Body
from . import store

router = APIRouter(prefix="/core/legal/rules", tags=["core-legal-rules"])

@router.get("")
def get():
    return store.get()

@router.post("")
def save(payload: Dict[str, Any] = Body(...)):
    return store.save(payload or {})
