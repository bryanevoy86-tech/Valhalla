from __future__ import annotations

from fastapi import APIRouter, HTTPException
from .schemas import MonthlyReportRequest, MonthlyReportListResponse
from . import service

router = APIRouter(prefix="/core/reports", tags=["core-reports"])


@router.post("/monthly")
def monthly(payload: MonthlyReportRequest):
    return service.build_monthly_report(month=payload.month, include_details=payload.include_details, meta=payload.meta)


@router.get("/monthly", response_model=MonthlyReportListResponse)
def list_monthly(limit: int = 25):
    return {"items": service.list_monthly(limit=limit)}


@router.get("/monthly/{report_id}")
def get_one(report_id: str):
    x = service.get_monthly(report_id)
    if not x:
        raise HTTPException(status_code=404, detail="report not found")
    return x
