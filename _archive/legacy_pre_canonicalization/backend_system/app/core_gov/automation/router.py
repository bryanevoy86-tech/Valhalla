from __future__ import annotations

from fastapi import APIRouter, HTTPException
from typing import Optional

from .schemas import RunRequest, RunListResponse
from . import service

router = APIRouter(prefix="/core/automation", tags=["core-automation"])


@router.post("/run")
def run(payload: RunRequest):
    return service.run_house_ops(run_type=payload.run_type, month=payload.month, meta=payload.meta)


@router.get("/runs", response_model=RunListResponse)
def runs(limit: int = 25):
    return {"items": service.list_runs(limit=limit)}


@router.get("/runs/{run_id}")
def get_one(run_id: str):
    x = service.get_run(run_id)
    if not x:
        raise HTTPException(status_code=404, detail="run not found")
    return x
