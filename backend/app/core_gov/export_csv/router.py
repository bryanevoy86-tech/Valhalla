from __future__ import annotations

from fastapi import APIRouter, HTTPException
from . import service

router = APIRouter(prefix="/core/export_csv", tags=["core-export-csv"])


@router.get("/receipts")
def receipts(limit: int = 500):
    return service.receipts_csv(limit=limit)


@router.get("/bank")
def bank(status: str = "", limit: int = 500):
    return service.bank_csv(status=status, limit=limit)


@router.get("/monthly_report")
def monthly_report(month: str):
    if not month:
        raise HTTPException(status_code=400, detail="month required YYYY-MM")
    return service.monthly_report_csv(month=month)
