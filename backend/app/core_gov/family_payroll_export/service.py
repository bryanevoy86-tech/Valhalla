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

def year_summary(year: int) -> Dict[str, Any]:
    warnings = []
    try:
        from backend.app.core_gov.family_payroll import service as fpsvc  # type: ignore
        people = fpsvc.list_people(status="active")
        entries = fpsvc.list_entries()
    except Exception as e:
        return {"warnings": [f"family_payroll unavailable: {type(e).__name__}: {e}"], "summary": []}

    y = f"{int(year):04d}-"
    entries = [e for e in entries if (e.get("date") or "").startswith(y)]

    by_person = {}
    for p in people:
        by_person[p["id"]] = {"person_id": p["id"], "name": p.get("name",""), "pay_total": 0.0, "deductions_total": 0.0, "task_count": 0, "meal_count": 0}

    for e in entries:
        pid = e.get("person_id")
        if pid not in by_person:
            by_person[pid] = {"person_id": pid, "name": "", "pay_total": 0.0, "deductions_total": 0.0, "task_count": 0, "meal_count": 0}
        if e.get("entry_type") == "pay":
            by_person[pid]["pay_total"] += float(e.get("amount") or 0.0)
        elif e.get("entry_type") == "deduction":
            by_person[pid]["deductions_total"] += float(e.get("amount") or 0.0)
        elif e.get("entry_type") == "task":
            by_person[pid]["task_count"] += 1
        elif e.get("entry_type") == "meal":
            by_person[pid]["meal_count"] += 1

    summary = list(by_person.values())
    summary.sort(key=lambda x: x.get("name",""))
    return {"year": int(year), "summary": summary, "warnings": warnings}

def export_entries_csv(year: int) -> Dict[str, Any]:
    try:
        from backend.app.core_gov.family_payroll import service as fpsvc  # type: ignore
        entries = fpsvc.list_entries()
    except Exception as e:
        return {"csv": "", "warnings": [f"family_payroll unavailable: {type(e).__name__}: {e}"]}

    y = f"{int(year):04d}-"
    rows = [e for e in entries if (e.get("date") or "").startswith(y)]
    fields = ["id","person_id","entry_type","date","amount","description","deduction_type","meal_log"]
    return {"csv": _to_csv(rows, fields), "warnings": []}
