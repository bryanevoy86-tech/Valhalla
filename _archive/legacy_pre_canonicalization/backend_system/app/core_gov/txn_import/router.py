from __future__ import annotations

from typing import Any, Dict
from fastapi import APIRouter, Body, HTTPException
from . import service

router = APIRouter(prefix="/core/txn_import", tags=["core-txn-import"])

@router.post("/csv")
def import_csv(
    payload: Dict[str, Any] = Body(...),
):
    try:
        return service.import_csv(
            csv_text=payload.get("csv_text",""),
            account_id=payload.get("account_id",""),
            date_col=payload.get("date_col","date"),
            amount_col=payload.get("amount_col","amount"),
            desc_col=payload.get("desc_col","description"),
            merchant_col=payload.get("merchant_col","merchant"),
            kind_default=payload.get("kind_default","expense"),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
