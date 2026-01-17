from __future__ import annotations

import csv
from io import StringIO
from typing import Any, Dict, List

FIELDS = ["id","kind","date","amount","merchant","description","category","account_id","obligation_id","receipt_id"]

def ledger_to_csv(date_from: str = "", date_to: str = "") -> Dict[str, Any]:
    try:
        from backend.app.core_gov.ledger import service as lsvc  # type: ignore
        items = lsvc.list_items(date_from=date_from, date_to=date_to)
    except Exception as e:
        return {"csv": "", "warnings": [f"ledger unavailable: {type(e).__name__}: {e}"]}

    buf = StringIO()
    w = csv.DictWriter(buf, fieldnames=FIELDS)
    w.writeheader()
    for it in items:
        w.writerow({k: it.get(k,"") for k in FIELDS})
    return {"csv": buf.getvalue(), "count": len(items), "warnings": []}
