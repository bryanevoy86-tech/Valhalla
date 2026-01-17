from __future__ import annotations

from fastapi import APIRouter
from . import service

router = APIRouter(prefix="/core/csv_export", tags=["core-csv-export"])

@router.get("/ledger")
def ledger(date_from: str = "", date_to: str = ""):
    return service.ledger_to_csv(date_from=date_from, date_to=date_to)
