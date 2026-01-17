from __future__ import annotations

from typing import Any, Dict
from fastapi import APIRouter, HTTPException
from . import service, allocator, autoplan, health

router = APIRouter(prefix="/core/vaults", tags=["core-vaults"])


@router.post("")
def create(name: str, target: float = 0.0, balance: float = 0.0, category: str = "general", notes: str = ""):
    try:
        return service.create(name=name, target=target, balance=balance, category=category, notes=notes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("")
def list_items():
    return {"items": service.list_items()}


@router.patch("/{vault_id}")
def patch(vault_id: str, patch: Dict[str, Any]):
    try:
        return service.patch(vault_id, patch)
    except KeyError:
        raise HTTPException(status_code=404, detail="vault not found")


@router.post("/{vault_id}/deposit")
def deposit(vault_id: str, amount: float, note: str = ""):
    try:
        return service.deposit(vault_id, amount=amount, note=note)
    except KeyError:
        raise HTTPException(status_code=404, detail="vault not found")


@router.post("/{vault_id}/withdraw")
def withdraw(vault_id: str, amount: float, note: str = ""):
    try:
        return service.withdraw(vault_id, amount=amount, note=note)
    except KeyError:
        raise HTTPException(status_code=404, detail="vault not found")


@router.get("/suggest_funding")
def suggest_funding(days: int = 30):
    return allocator.suggest_funding(days=days)


@router.get("/autoplan_obligations")
def autoplan_obligations(monthly_buffer_pct: float = 0.10):
    return autoplan.build_obligation_vault_plan(monthly_buffer_pct=monthly_buffer_pct)


@router.post("/autoplan_obligations/create_missing_vaults")
def autoplan_create_missing(monthly_buffer_pct: float = 0.10):
    plan = autoplan.build_obligation_vault_plan(monthly_buffer_pct=monthly_buffer_pct)
    return autoplan.create_missing_vaults(plan)


@router.get("/health")
def vault_health(days: int = 30):
    return health.score_buffers(days=days)
