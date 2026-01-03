from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, HTTPException

from .schemas import CreditProfileUpsert, CreditAccountCreate, CreditListResponse, UtilUpdate
from . import service

router = APIRouter(prefix="/core/credit", tags=["core-credit"])


@router.post("/profile")
def upsert_profile(payload: CreditProfileUpsert):
    return service.upsert_profile(payload.model_dump())


@router.post("/accounts")
def create_account(payload: CreditAccountCreate):
    try:
        return service.create_account(payload.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=CreditListResponse)
def get_all(status: Optional[str] = None, account_type: Optional[str] = None):
    accounts = service.list_accounts(status=status, account_type=account_type)
    return {"profile": service.upsert_profile({}), "accounts": accounts, "totals": service.totals()}


@router.post("/accounts/utilization")
def update_util(payload: UtilUpdate):
    try:
        return service.update_utilization(payload.account_id, balance=float(payload.balance), credit_limit=payload.credit_limit)
    except KeyError:
        raise HTTPException(status_code=404, detail="account not found")


@router.get("/recommend_next")
def recommend_next():
    return {"steps": service.recommend_next_steps(), "totals": service.totals()}


@router.post("/tasks")
def add_task(title: str, due_date: str, priority: str = "B"):
    try:
        return service.add_task(title=title, due_date=due_date, priority=priority)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tasks")
def list_tasks(status: Optional[str] = None):
    return {"items": service.list_tasks(status=status)}
