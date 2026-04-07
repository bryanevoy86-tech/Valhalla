from datetime import datetime
from pathlib import Path
import json

BASE = Path("EIA")
BASE.mkdir(exist_ok=True)

def build_monthly_packet(month: str, payload: dict | None = None) -> dict:
    payload = payload or {}
    month_dir = BASE / month
    month_dir.mkdir(parents=True, exist_ok=True)

    packet = {
        "month": month,
        "generated_at": datetime.utcnow().isoformat(),
        "income_summary": payload.get("income_summary", []),
        "expense_summary": payload.get("expense_summary", []),
        "receipt_index": payload.get("receipt_index", []),
        "bank_checklist": payload.get("bank_checklist", []),
        "notes": payload.get("notes", []),
        "status": "PACKET_READY",
    }

    out = month_dir / f"EIA_PACKET_{month}.json"
    out.write_text(json.dumps(packet, indent=2), encoding="utf-8")

    return {
        "ok": True,
        "path": str(out),
        "packet": packet,
    }
