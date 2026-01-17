from __future__ import annotations

from typing import Any, Dict, List

def tag_ledger(ledger_id: str, tax_code: str) -> Dict[str, Any]:
    if not ledger_id:
        raise ValueError("ledger_id required")
    if not tax_code:
        raise ValueError("tax_code required")

    try:
        from backend.app.core_gov.ledger import store as lst  # type: ignore
        items = lst.list_items()
        tgt = next((x for x in items if x.get("id") == ledger_id), None)
        if not tgt:
            raise KeyError("ledger not found")
        tgt.setdefault("meta", {})
        tgt["meta"]["tax_code"] = tax_code.strip().upper()
        lst.save_items(items)
        return tgt
    except KeyError:
        raise
    except Exception as e:
        raise RuntimeError(f"ledger tag failed: {type(e).__name__}: {e}")

def tag_receipt(receipt_id: str, tax_code: str) -> Dict[str, Any]:
    if not receipt_id:
        raise ValueError("receipt_id required")
    if not tax_code:
        raise ValueError("tax_code required")

    try:
        from backend.app.core_gov.receipts import store as rst  # type: ignore
        items = rst.list_items()
        tgt = next((x for x in items if x.get("id") == receipt_id), None)
        if not tgt:
            raise KeyError("receipt not found")
        tgt.setdefault("meta", {})
        tgt["meta"]["tax_code"] = tax_code.strip().upper()
        rst.save_items(items)
        return tgt
    except KeyError:
        raise
    except Exception as e:
        raise RuntimeError(f"receipt tag failed: {type(e).__name__}: {e}")
