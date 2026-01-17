from __future__ import annotations

import csv
from io import StringIO
from typing import Any, Dict, List

def import_csv(csv_text: str, account_id: str = "", date_col: str = "date", amount_col: str = "amount", desc_col: str = "description", merchant_col: str = "merchant", kind_default: str = "expense") -> Dict[str, Any]:
    if not (csv_text or "").strip():
        raise ValueError("csv_text required")

    reader = csv.DictReader(StringIO(csv_text))
    rows = list(reader)
    if not rows:
        return {"imported": 0, "warnings": ["no rows parsed"], "items": []}

    warnings: List[str] = []
    created = 0
    items = []

    try:
        from backend.app.core_gov.ledger import service as lsvc  # type: ignore
    except Exception as e:
        return {"imported": 0, "warnings": [f"ledger unavailable: {type(e).__name__}: {e}"], "items": []}

    for r in rows:
        try:
            d = (r.get(date_col) or "").strip()
            a = float((r.get(amount_col) or "0").strip() or 0.0)
            desc = (r.get(desc_col) or "").strip()
            merch = (r.get(merchant_col) or "").strip()
            kind = kind_default
            if a < 0:
                # common banking exports store expenses as negative
                kind = "expense"
                a = abs(a)
            else:
                # could be income, leave as default unless user sets
                kind = kind_default

            rec = lsvc.create(kind=kind, date=d, amount=a, description=desc, merchant=merch, account_id=account_id)
            items.append(rec)
            created += 1
        except Exception as e:
            warnings.append(f"row skipped: {type(e).__name__}: {e}")

    return {"imported": created, "warnings": warnings[:200], "items": items[:200]}
