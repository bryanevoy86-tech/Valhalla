from __future__ import annotations

def infer_category(merchant: str) -> str:
    try:
        from backend.app.core_gov.ledger_rules import service as rsvc
        return rsvc.apply(description=merchant or "")
    except Exception:
        return ""
