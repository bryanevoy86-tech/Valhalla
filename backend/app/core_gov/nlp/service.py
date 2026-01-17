from __future__ import annotations
from typing import Any, Dict
from .parse_rules import infer_currency, infer_cadence, extract_amount, extract_date, extract_due_day

def parse(text: str) -> Dict[str, Any]:
    t = (text or "").strip()
    if not t:
        return {"ok": False, "error": "text required"}

    lower = t.lower()
    kind = "note"
    if any(w in lower for w in ["bill", "internet", "rent", "hydro", "water", "phone", "insurance"]):
        kind = "bill"
    if any(w in lower for w in ["i'm out", "out of", "running low", "need to buy", "toilet paper", "milk"]):
        kind = "need"
    if any(w in lower for w in ["appointment", "event", "on ", "tomorrow", "next week"]):
        # only switch if not obviously a bill/need
        if kind == "note":
            kind = "event"

    amount = extract_amount(t)
    date = extract_date(t)
    due_day = extract_due_day(t)
    cadence = infer_cadence(t)
    currency = infer_currency(t)

    return {
        "ok": True,
        "kind": kind,
        "raw": t,
        "fields": {
            "amount": amount,
            "currency": currency,
            "date": date,
            "due_day": due_day,
            "cadence": cadence,
        }
    }
