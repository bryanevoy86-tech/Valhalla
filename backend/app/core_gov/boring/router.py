from __future__ import annotations

from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException

from .schemas import BoringEngineCreate, RunCreate, EngineListResponse, RunListResponse, SummaryResponse
from . import service

router = APIRouter(prefix="/core/boring", tags=["core-boring"])


@router.post("/engines")
def create_engine(payload: BoringEngineCreate):
    try:
        return service.create_engine(payload.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/engines", response_model=EngineListResponse)
def list_engines(status: Optional[str] = None, tag: Optional[str] = None):
    return {"items": service.list_engines(status=status, tag=tag)}


@router.get("/engines/{engine_id}")
def get_engine(engine_id: str):
    e = service.get_engine(engine_id)
    if not e:
        raise HTTPException(status_code=404, detail="engine not found")
    return e


@router.patch("/engines/{engine_id}")
def patch_engine(engine_id: str, patch: Dict[str, Any]):
    try:
        return service.patch_engine(engine_id, patch)
    except KeyError:
        raise HTTPException(status_code=404, detail="engine not found")


@router.post("/runs")
def create_run(payload: RunCreate):
    try:
        return service.create_run(payload.model_dump())
    except KeyError:
        raise HTTPException(status_code=404, detail="engine not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/runs", response_model=RunListResponse)
def list_runs(engine_id: Optional[str] = None, status: Optional[str] = None):
    return {"items": service.list_runs(engine_id=engine_id, status=status)}


@router.patch("/runs/{run_id}")
def patch_run(run_id: str, patch: Dict[str, Any]):
    try:
        return service.patch_run(run_id, patch)
    except KeyError:
        raise HTTPException(status_code=404, detail="run not found")


@router.get("/summary", response_model=SummaryResponse)
def summary():
    return service.summary()
