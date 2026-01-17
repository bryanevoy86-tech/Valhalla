from __future__ import annotations

import csv
import io
from typing import Any, Dict, List


def _to_csv(rows: List[Dict[str, Any]], fields: List[str]) -> str:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fields, extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow(r)
    return buf.getvalue()


def receipts_csv(limit: int = 500) -> Dict[str, Any]:
    warnings = []
    try:
        from backend.app.core_gov.receipts import service as rsvc  # type: ignore
        rows = rsvc.list_items()[: int(limit or 500)]
    except Exception as e:
        return {"csv": "", "warnings": [f"receipts unavailable: {type(e).__name__}: {e}"]}

    fields = ["id","date","vendor","total","tax","tip","currency","category","status","source","notes"]
    return {"csv": _to_csv(rows, fields), "warnings": warnings}


def bank_csv(status: str = "", limit: int = 500) -> Dict[str, Any]:
    warnings = []
    try:
        from backend.app.core_gov.bank import service as bsvc  # type: ignore
        rows = bsvc.list_txns(status=status, limit=int(limit or 500))
    except Exception as e:
        return {"csv": "", "warnings": [f"bank unavailable: {type(e).__name__}: {e}"]}

    fields = ["id","date","description","amount","currency","txn_type","account","status","external_id","notes"]
    return {"csv": _to_csv(rows, fields), "warnings": warnings}


def monthly_report_csv(month: str) -> Dict[str, Any]:
    warnings = []
    try:
        from backend.app.core_gov.reports import service as rsvc  # type: ignore
        rec = rsvc.build_monthly_report(month=month, include_details=False, meta={"format": "csv_export"})
        report = rec.get("report") or {}
        plan = report.get("plan") or {}
        actuals = report.get("actuals") or {}
        var = report.get("variance") or {}
    except Exception as e:
        return {"csv": "", "warnings": [f"reports unavailable: {type(e).__name__}: {e}"]}

    rows = [{
        "month": month,
        "plan_total": plan.get("grand_est_total", ""),
        "actual_total": actuals.get("grand_total", ""),
        "payments_total": actuals.get("payments_total",""),
        "receipts_total": actuals.get("receipts_total",""),
        "delta": var.get("delta_actual_minus_plan",""),
    }]
    fields = ["month","plan_total","actual_total","payments_total","receipts_total","delta"]
    return {"csv": _to_csv(rows, fields), "warnings": warnings}
