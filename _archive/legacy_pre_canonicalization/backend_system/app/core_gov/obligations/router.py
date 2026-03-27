from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, Query

from .schemas import ObligationCreate, ObligationListResponse, AutopayVerifyRequest
from . import service
from . import autopay as autopay_service

router = APIRouter(prefix="/core/obligations", tags=["core-obligations"])


# ========== PACK 1: Core CRUD ==========

@router.post("")
def create_obligation(payload: ObligationCreate):
    try:
        return service.create_obligation(payload.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=ObligationListResponse)
def list_obligations(
    status: Optional[str] = None,
    frequency: Optional[str] = None,
    category: Optional[str] = None,
    pay_from: Optional[str] = None,
):
    return {"items": service.list_obligations(status=status, frequency=frequency, category=category, pay_from=pay_from)}


@router.get("/{obligation_id}")
def get_obligation(obligation_id: str):
    o = service.get_obligation(obligation_id)
    if not o:
        raise HTTPException(status_code=404, detail="obligation not found")
    return o


@router.patch("/{obligation_id}")
def patch_obligation(obligation_id: str, patch: Dict[str, Any]):
    try:
        return service.patch_obligation(obligation_id, patch)
    except KeyError:
        raise HTTPException(status_code=404, detail="obligation not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{obligation_id}/verify_autopay")
def verify_autopay(obligation_id: str, payload: AutopayVerifyRequest):
    try:
        return service.verify_autopay(obligation_id, payload.model_dump(exclude_none=True))
    except KeyError:
        raise HTTPException(status_code=404, detail="obligation not found")


# ========== PACK 2: Recurrence Engine + Upcoming Runs ==========

@router.post("/runs/generate")
def generate_runs(
    start_date: str,
    end_date: str,
):
    try:
        return service.save_upcoming_runs(start_date=start_date, end_date=end_date)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/runs")
def list_runs(limit: int = Query(default=200, ge=1, le=500)):
    return {"items": service.list_runs(limit=limit)}


@router.get("/upcoming_30")
def upcoming_30():
    s = date.today().isoformat()
    e = (date.today() + timedelta(days=30)).isoformat()
    try:
        return {"items": service.generate_upcoming(s, e), "start_date": s, "end_date": e}
    except Exception as e2:
        raise HTTPException(status_code=400, detail=str(e2))


# ========== PACK 3: Reserve Locking + "Are We Covered?" ==========

@router.post("/reserves/recalculate")
def recalc(buffer_multiplier: float = 1.25):
    try:
        return service.recalc_reserve_state(buffer_multiplier=buffer_multiplier)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/reserves")
def reserves():
    return service.get_reserve_state()


@router.get("/status")
def status(buffer_multiplier: float = 1.25):
    try:
        return service.obligations_status(buffer_multiplier=buffer_multiplier)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{obligation_id}/autopay_guide")
def autopay_guide(obligation_id: str):
    try:
        return service.autopay_setup_guide(obligation_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="obligation not found")


@router.post("/{obligation_id}/autopay_enable")
def autopay_enable(obligation_id: str, enabled: bool = True):
    try:
        return autopay_service.set_autopay_enabled(obligation_id, enabled=enabled)
    except KeyError:
        raise HTTPException(status_code=404, detail="obligation not found")


@router.post("/{obligation_id}/autopay_verify")
def autopay_verify(obligation_id: str, verified: bool = True, confirmation_ref: str = ""):
    try:
        return autopay_service.set_autopay_verified(obligation_id, verified=verified, confirmation_ref=confirmation_ref)
    except KeyError:
        raise HTTPException(status_code=404, detail="obligation not found")


@router.post("/{obligation_id}/autopay_verification_followup")
def autopay_verification_followup(obligation_id: str, days_out: int = 7):
    try:
        ok = autopay_service.create_verification_followup(obligation_id, days_out=days_out)
        return {"created": ok}
    except KeyError:
        raise HTTPException(status_code=404, detail="obligation not found")
