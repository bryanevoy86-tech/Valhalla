from __future__ import annotations

import csv
import io
from typing import Any, Dict, List, Tuple


def parse_csv(text: str, mapping: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    mapping example:
      {
        "date": "Date",
        "description": "Description",
        "amount": "Amount",
        "currency": "Currency",
        "account": "Account",
        "external_id": "Transaction ID",
        "txn_type": "Type"   # optional
      }
    """
    if not text or not text.strip():
        return []

    rdr = csv.DictReader(io.StringIO(text))
    out: List[Dict[str, Any]] = []

    for row in rdr:
        def g(key: str, default=""):
            col = mapping.get(key) or ""
            if not col:
                return default
            return (row.get(col) or default).strip()

        # amount normalization: support "(123.45)" and "$123.45"
        raw_amt = g("amount", "0")
        raw_amt = raw_amt.replace("$", "").replace(",", "").strip()
        if raw_amt.startswith("(") and raw_amt.endswith(")"):
            raw_amt = "-" + raw_amt[1:-1]
        try:
            amt = float(raw_amt)
        except Exception:
            amt = 0.0

        payload = {
            "date": g("date"),
            "description": g("description"),
            "amount": amt,
            "currency": g("currency", "CAD") or "CAD",
            "txn_type": g("txn_type", "unknown") or "unknown",
            "account": g("account", ""),
            "external_id": g("external_id", ""),
            "status": "new",
            "tags": [],
            "notes": "",
            "meta": {"csv_row": row},
        }

        # minimal validation here; bank.service.create() enforces required fields
        out.append(payload)

    return out
