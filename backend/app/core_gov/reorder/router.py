from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from .schemas import ReorderRuleCreate, RuleListResponse, EvalResponse
from . import service
try:
    from . import service as scan_svc  # type: ignore
    HAS_SCAN = True
except Exception:
    HAS_SCAN = False

router = APIRouter(prefix="/core/reorder", tags=["core-reorder"])


@router.post("/rules")
def create_rule(payload: ReorderRuleCreate):
    try:
        return service.create_rule(payload.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/rules", response_model=RuleListResponse)
def list_rules(status: Optional[str] = None):
    return {"items": service.list_rules(status=status)}


@router.post("/evaluate", response_model=EvalResponse)
def evaluate(run_actions: bool = Query(default=True)):
    return service.evaluate(run_actions=run_actions)


@router.post("/scan")
def scan(desired_by_days: int = 3, dry_run: bool = True):
    try:
        # Try to import the new scan service
        from . import service_new  # type: ignore
        return service_new.scan_and_create(desired_by_days=desired_by_days, dry_run=dry_run)
    except Exception:
        # Fallback to placeholder
        return {"error": "scan service not available"}

