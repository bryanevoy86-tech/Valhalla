from __future__ import annotations

from fastapi import APIRouter, HTTPException
from . import service

router = APIRouter(prefix="/core/tax_tagging", tags=["core-tax-tagging"])

@router.post("/ledger")
def tag_ledger(ledger_id: str, tax_code: str):
    try:
        return service.tag_ledger(ledger_id=ledger_id, tax_code=tax_code)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except KeyError:
        raise HTTPException(status_code=404, detail="ledger not found")
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/receipt")
def tag_receipt(receipt_id: str, tax_code: str):
    try:
        return service.tag_receipt(receipt_id=receipt_id, tax_code=tax_code)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except KeyError:
        raise HTTPException(status_code=404, detail="receipt not found")
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
