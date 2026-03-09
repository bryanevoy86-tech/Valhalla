from __future__ import annotations
from typing import Any, Dict
from .service import parse

def intent(text: str) -> Dict[str, Any]:
    p = parse(text=text)
    if not p.get("ok"):
        return p
    kind = p.get("kind")
    f = p.get("fields") or {}
    # minimal normalized payloads
    if kind == "bill":
        return {"ok": True, "intent": "bill.create_candidate", "candidate": {
            "name": _guess_name(text),
            "payee": _guess_payee(text),
            "amount": f.get("amount") or 0.0,
            "currency": f.get("currency") or "CAD",
            "cadence": f.get("cadence") or "monthly",
            "due_day": int(f.get("due_day") or 1),
            "notes": text,
        }}
    if kind == "need":
        return {"ok": True, "intent": "shopping.quick_add_candidate", "candidate": {
            "name": _guess_need(text),
            "est_total": f.get("amount") or 0.0,
            "category": "household",
            "notes": text,
        }}
    if kind == "event":
        return {"ok": True, "intent": "schedule.create_candidate", "candidate": {
            "title": text[:80],
            "date": f.get("date") or "",
            "time": "",
            "duration_min": 60,
            "kind": "personal",
            "notes": text,
        }}
    return {"ok": True, "intent": "note", "candidate": {"text": text}}

def _guess_name(text: str) -> str:
    t = (text or "").strip()
    for k in ["internet", "rent", "water", "hydro", "phone", "insurance"]:
        if k in t.lower():
            return k.title()
    return "Bill"

def _guess_payee(text: str) -> str:
    # v1: unknown unless explicitly written like "to Rogers"
    t = (text or "")
    if " to " in t.lower():
        parts = t.split(" to ")
        if len(parts) >= 2:
            return parts[-1].strip()[:60]
    return ""

def _guess_need(text: str) -> str:
    t = (text or "").lower()
    for k in ["toilet paper", "milk", "bread", "eggs", "soap"]:
        if k in t:
            return k
    # fallback: remove leading phrases
    for pref in ["i'm out of", "out of", "running low on", "need to buy"]:
        if pref in t:
            return t.split(pref, 1)[1].strip()
    return (text or "").strip()[:60]
