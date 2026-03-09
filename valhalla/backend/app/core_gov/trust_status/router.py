from __future__ import annotations
from typing import Any, Dict
from fastapi import APIRouter, Body
from . import store
from .reminders import push_reminders

router = APIRouter(prefix="/core/trust/status", tags=["core-trust-status"])

@router.get("")
def get():
    return store.get()

@router.post("")
def save(payload: Dict[str, Any] = Body(...)):
    return store.save(payload or {})

@router.post("/push_reminders")
def push():
    return push_reminders()

