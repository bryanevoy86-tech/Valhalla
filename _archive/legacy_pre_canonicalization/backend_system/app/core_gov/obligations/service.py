from __future__ import annotations

import uuid
import calendar
from datetime import date, datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from . import store


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _norm(s: str) -> str:
    return (s or "").strip()


def _dedupe(tags: List[str]) -> List[str]:
    out, seen = [], set()
    for t in tags or []:
        t2 = _norm(t)
        if t2 and t2 not in seen:
            seen.add(t2)
            out.append(t2)
    return out


def _parse_date(s: str) -> date:
    # expects YYYY-MM-DD
    return date.fromisoformat(s)


def _safe_day(year: int, month: int, dom: int) -> int:
    last = calendar.monthrange(year, month)[1]
    return max(1, min(int(dom), last))


def _add_months(d: date, months: int) -> date:
    y = d.year + (d.month - 1 + months) // 12
    m = (d.month - 1 + months) % 12 + 1
    day = _safe_day(y, m, d.day)
    return date(y, m, day)


def _default_recurrence(frequency: str, due_day: int, tz: str) -> Dict[str, Any]:
    # weekly/biweekly will use day_of_week = Monday by default (0)
    freq = frequency or "monthly"
    rec = {
        "frequency": freq,
        "day_of_month": int(due_day or 1),
        "day_of_week": 0,
        "interval": 1,
        "start_date": "",
        "timezone": tz or "America/Toronto",
    }
    return rec


def create_obligation(payload: Dict[str, Any]) -> Dict[str, Any]:
    name = _norm(payload.get("name") or "")
    if not name:
        raise ValueError("name is required")
    amount = payload.get("amount", None)
    if amount is None:
        raise ValueError("amount is required")
    try:
        amount_f = float(amount)
    except Exception:
        raise ValueError("amount must be a number")
    if amount_f < 0:
        raise ValueError("amount must be >= 0")

    frequency = payload.get("frequency") or "monthly"
    due_day = int(payload.get("due_day") or 1)
    if due_day < 1 or due_day > 31:
        raise ValueError("due_day must be 1-31")

    rec = payload.get("recurrence") or None
    if rec is None:
        rec = _default_recurrence(frequency, due_day, "America/Toronto")
    else:
        # normalize
        rec = dict(rec)
        rec["frequency"] = rec.get("frequency") or frequency
        rec["day_of_month"] = int(rec.get("day_of_month") or due_day)
        rec["day_of_week"] = int(rec.get("day_of_week") or 0)
        rec["interval"] = int(rec.get("interval") or 1)
        rec["start_date"] = _norm(rec.get("start_date") or "")
        rec["timezone"] = rec.get("timezone") or "America/Toronto"

    items = store.list_obligations()
    now = _utcnow_iso()
    oid = "ob_" + uuid.uuid4().hex[:12]

    autopay = payload.get("autopay") or {}
    autopay = {
        "enabled": bool(autopay.get("enabled", False)),
        "verified": bool(autopay.get("verified", False)),
        "method": autopay.get("method") or "manual",
        "payee": _norm(autopay.get("payee") or ""),
        "reference": _norm(autopay.get("reference") or ""),
        "notes": autopay.get("notes") or "",
    }

    rec_out = {
        "id": oid,
        "name": name,
        "amount": amount_f,
        "currency": _norm(payload.get("currency") or "CAD") or "CAD",
        "due_day": due_day,
        "frequency": frequency,
        "next_due_date": _norm(payload.get("next_due_date") or ""),
        "category": _norm(payload.get("category") or "household") or "household",
        "priority": payload.get("priority") or "A",
        "status": payload.get("status") or "active",
        "pay_from": _norm(payload.get("pay_from") or "personal") or "personal",
        "autopay": autopay,
        "recurrence": rec,
        "tags": _dedupe(payload.get("tags") or []),
        "meta": payload.get("meta") or {},
        "created_at": now,
        "updated_at": now,
    }

    items.append(rec_out)
    store.save_obligations(items)

    # optional audit
    try:
        from backend.app.core_gov.audit import service as audit_service  # type: ignore
        audit_service.log({
            "event_type": "system",
            "level": "info",
            "message": f"OBLIGATION created: {name}",
            "actor": "api",
            "ref_type": "obligation",
            "ref_id": oid,
            "meta": {"frequency": frequency, "amount": amount_f, "currency": rec_out["currency"]},
        })
    except Exception:
        pass

    return rec_out


def list_obligations(
    status: Optional[str] = None,
    frequency: Optional[str] = None,
    category: Optional[str] = None,
    pay_from: Optional[str] = None,
) -> List[Dict[str, Any]]:
    items = store.list_obligations()
    if status:
        items = [o for o in items if o.get("status") == status]
    if frequency:
        items = [o for o in items if o.get("frequency") == frequency]
    if category:
        items = [o for o in items if o.get("category") == category]
    if pay_from:
        items = [o for o in items if o.get("pay_from") == pay_from]
    return items


def get_obligation(obligation_id: str) -> Optional[Dict[str, Any]]:
    for o in store.list_obligations():
        if o["id"] == obligation_id:
            return o
    return None


def patch_obligation(obligation_id: str, patch: Dict[str, Any]) -> Dict[str, Any]:
    items = store.list_obligations()
    tgt = None
    for o in items:
        if o["id"] == obligation_id:
            tgt = o
            break
    if not tgt:
        raise KeyError("obligation not found")

    # safe fields
    for k in ["name", "frequency", "category", "priority", "status", "pay_from", "currency"]:
        if k in patch:
            tgt[k] = _norm(patch.get(k) or "") if k in ("name","category","pay_from","currency") else patch.get(k)

    if "amount" in patch:
        try:
            a = float(patch.get("amount"))
        except Exception:
            raise ValueError("amount must be a number")
        if a < 0:
            raise ValueError("amount must be >= 0")
        tgt["amount"] = a

    if "due_day" in patch:
        d = int(patch.get("due_day") or 1)
        if d < 1 or d > 31:
            raise ValueError("due_day must be 1-31")
        tgt["due_day"] = d

    if "next_due_date" in patch:
        tgt["next_due_date"] = _norm(patch.get("next_due_date") or "")

    if "tags" in patch:
        tgt["tags"] = _dedupe(patch.get("tags") or [])
    if "meta" in patch:
        tgt["meta"] = patch.get("meta") or {}

    # autopay patch
    if "autopay" in patch:
        ap = dict(patch.get("autopay") or {})
        if "enabled" in ap:
            ap["enabled"] = bool(ap.get("enabled"))
        if "verified" in ap:
            ap["verified"] = bool(ap.get("verified"))
        if "method" in ap:
            ap["method"] = ap.get("method") or "manual"
        if "payee" in ap:
            ap["payee"] = _norm(ap.get("payee") or "")
        if "reference" in ap:
            ap["reference"] = _norm(ap.get("reference") or "")
        if "notes" in ap:
            ap["notes"] = ap.get("notes") or ""
        tgt["autopay"] = ap

    # recurrence patch (partial)
    if "recurrence" in patch:
        rec = dict(patch.get("recurrence") or {})
        if not rec.get("frequency"):
            rec["frequency"] = tgt.get("frequency") or "monthly"
        if rec.get("day_of_month") is None:
            rec["day_of_month"] = tgt.get("due_day") or 1
        rec["day_of_month"] = int(rec.get("day_of_month") or 1)
        rec["day_of_week"] = int(rec.get("day_of_week") or 0)
        rec["interval"] = int(rec.get("interval") or 1)
        rec["start_date"] = _norm(rec.get("start_date") or "")
        rec["timezone"] = rec.get("timezone") or "America/Toronto"
        tgt["recurrence"] = rec

    tgt["updated_at"] = _utcnow_iso()
    store.save_obligations(items)
    return tgt


def verify_autopay(obligation_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    items = store.list_obligations()
    tgt = None
    for o in items:
        if o["id"] == obligation_id:
            tgt = o
            break
    if not tgt:
        raise KeyError("obligation not found")

    ap = tgt.get("autopay") or {}
    ap["verified"] = bool(payload.get("verified", True))
    if payload.get("method") is not None:
        ap["method"] = payload.get("method") or ap.get("method") or "manual"
    if payload.get("payee") is not None:
        ap["payee"] = _norm(payload.get("payee") or "")
    if payload.get("reference") is not None:
        ap["reference"] = _norm(payload.get("reference") or "")
    if payload.get("notes") is not None:
        ap["notes"] = payload.get("notes") or ""

    # if verified -> enabled true
    if ap["verified"]:
        ap["enabled"] = True

    tgt["autopay"] = ap
    tgt["updated_at"] = _utcnow_iso()
    store.save_obligations(items)

    # optional followup if not verified
    if not ap["verified"]:
        try:
            from backend.app.deals import followups_store  # type: ignore
            followups_store.create_followup({
                "title": f"AUTOPAY VERIFY: {tgt['name']}",
                "due_date": (date.today() + timedelta(days=2)).isoformat(),
                "priority": "A",
                "status": "open",
                "meta": {"obligation_id": obligation_id},
            })
        except Exception:
            pass

    return tgt


# ========== PACK 2: Recurrence Engine + Upcoming Runs ==========

def _next_due_from_recurrence(o: Dict[str, Any], from_date: date) -> date:
    rec = o.get("recurrence") or {}
    freq = rec.get("frequency") or o.get("frequency") or "monthly"
    interval = int(rec.get("interval") or 1)

    # explicit override
    if o.get("next_due_date"):
        try:
            nd = _parse_date(o["next_due_date"])
            if nd >= from_date:
                return nd
        except Exception:
            pass

    if freq in ("monthly", "quarterly", "annually"):
        dom = int(rec.get("day_of_month") or o.get("due_day") or 1)
        base = date(from_date.year, from_date.month, _safe_day(from_date.year, from_date.month, dom))
        if base < from_date:
            base = _add_months(base, 1)
        if freq == "quarterly":
            # step in 3-month increments
            while base < from_date:
                base = _add_months(base, 3 * interval)
            # ensure next quarter boundary by moving at least 3 months if we already used current month
            if base < from_date:
                base = _add_months(base, 3 * interval)
        if freq == "annually":
            # move to this year dom (or next)
            base = date(from_date.year, from_date.month, _safe_day(from_date.year, from_date.month, dom))
            # annual is defined by month in meta if provided, else use from_date month (simple v1)
            annual_month = int(o.get("meta", {}).get("annual_month") or from_date.month)
            base = date(from_date.year, annual_month, _safe_day(from_date.year, annual_month, dom))
            if base < from_date:
                base = date(from_date.year + interval, annual_month, _safe_day(from_date.year + interval, annual_month, dom))
        return base

    if freq in ("weekly", "biweekly"):
        dow = int(rec.get("day_of_week") or 0)  # 0=Mon
        # python weekday: Mon=0..Sun=6
        delta = (dow - from_date.weekday()) % 7
        base = from_date + timedelta(days=delta)
        if base < from_date:
            base = base + timedelta(days=7)
        if freq == "biweekly":
            base = base + timedelta(days=14 * (interval - 1))
        return base

    # fallback monthly
    dom = int(rec.get("day_of_month") or o.get("due_day") or 1)
    base = date(from_date.year, from_date.month, _safe_day(from_date.year, from_date.month, dom))
    if base < from_date:
        base = _add_months(base, 1)
    return base


def generate_upcoming(start_date: str, end_date: str) -> List[Dict[str, Any]]:
    s = _parse_date(start_date)
    e = _parse_date(end_date)
    if e < s:
        raise ValueError("end_date must be >= start_date")

    out: List[Dict[str, Any]] = []
    for o in store.list_obligations():
        if o.get("status") != "active":
            continue
        due = _next_due_from_recurrence(o, s)
        # add occurrences until end date (caps to avoid runaway)
        cap = 120
        while due <= e and cap > 0:
            out.append({
                "id": "run_" + uuid.uuid4().hex[:10],
                "obligation_id": o["id"],
                "name": o.get("name") or "",
                "amount": float(o.get("amount") or 0.0),
                "currency": o.get("currency") or "CAD",
                "due_date": due.isoformat(),
                "priority": o.get("priority") or "A",
                "pay_from": o.get("pay_from") or "personal",
                "autopay_enabled": bool((o.get("autopay") or {}).get("enabled", False)),
                "autopay_verified": bool((o.get("autopay") or {}).get("verified", False)),
                "status": "scheduled",
                "created_at": _utcnow_iso(),
            })

            rec = o.get("recurrence") or {}
            freq = rec.get("frequency") or o.get("frequency") or "monthly"
            interval = int(rec.get("interval") or 1)

            if freq == "weekly":
                due = due + timedelta(days=7 * interval)
            elif freq == "biweekly":
                due = due + timedelta(days=14 * interval)
            elif freq == "monthly":
                due = _add_months(due, 1 * interval)
            elif freq == "quarterly":
                due = _add_months(due, 3 * interval)
            elif freq == "annually":
                due = date(due.year + interval, due.month, _safe_day(due.year + interval, due.month, due.day))
            else:
                due = _add_months(due, 1)

            cap -= 1

    # sort by due_date then priority
    out.sort(key=lambda x: (x["due_date"], x.get("priority", "A")))
    return out


def save_upcoming_runs(start_date: str, end_date: str) -> Dict[str, Any]:
    runs = generate_upcoming(start_date, end_date)
    store.save_runs(runs)

    # optional audit
    try:
        from backend.app.core_gov.audit import service as audit_service  # type: ignore
        audit_service.log({
            "event_type": "system",
            "level": "info",
            "message": f"OBLIGATIONS runs generated: {len(runs)}",
            "actor": "api",
            "ref_type": "obligations_runs",
            "ref_id": "",
            "meta": {"start_date": start_date, "end_date": end_date},
        })
    except Exception:
        pass

    return {"ok": True, "count": len(runs), "start_date": start_date, "end_date": end_date}


def list_runs(limit: int = 200) -> List[Dict[str, Any]]:
    items = store.read_runs()
    return items[: max(1, min(limit, 500))]


# ========== PACK 3: Reserve Locking + "Are We Covered?" ==========

def _monthly_equivalent(o: Dict[str, Any]) -> float:
    amt = float(o.get("amount") or 0.0)
    freq = (o.get("frequency") or (o.get("recurrence") or {}).get("frequency") or "monthly")

    if freq == "weekly":
        return amt * 52.0 / 12.0
    if freq == "biweekly":
        return amt * 26.0 / 12.0
    if freq == "monthly":
        return amt
    if freq == "quarterly":
        return amt / 3.0
    if freq == "annually":
        return amt / 12.0
    return amt


def recalc_reserve_state(buffer_multiplier: float = 1.25, include_paused: bool = False) -> Dict[str, Any]:
    if buffer_multiplier < 1.0:
        raise ValueError("buffer_multiplier must be >= 1.0")

    obligations = store.list_obligations()
    active = []
    for o in obligations:
        if o.get("status") == "active" or (include_paused and o.get("status") == "paused"):
            active.append(o)

    monthly_required = 0.0
    autopay_verified = 0
    autopay_total = 0

    by_category: Dict[str, float] = {}
    for o in active:
        m = _monthly_equivalent(o)
        monthly_required += m
        cat = o.get("category") or "household"
        by_category[cat] = by_category.get(cat, 0.0) + m

        ap = o.get("autopay") or {}
        if ap.get("enabled"):
            autopay_total += 1
            if ap.get("verified"):
                autopay_verified += 1

    buffer_required = monthly_required * float(buffer_multiplier)
    state = {
        "monthly_required": round(monthly_required, 2),
        "buffer_multiplier": float(buffer_multiplier),
        "buffer_required": round(buffer_required, 2),
        "by_category": {k: round(v, 2) for k, v in by_category.items()},
        "autopay_verified": autopay_verified,
        "autopay_total": autopay_total,
        # coverage is best-effort: if capital module exists, we compare to "personal_cash"
        "coverage": {
            "available_cash": None,
            "covered": None,
            "note": "coverage requires capital module providing a personal cash balance",
        },
        "updated_at": _utcnow_iso(),
    }

    # best-effort: pull a personal cash number from capital module if it exists
    try:
        from backend.app.deals import capital_store  # type: ignore
        cap = capital_store.get_capital_state()
        # try common keys (safe; if not present, we just skip)
        available = cap.get("personal_cash", None) or cap.get("cash_personal", None) or cap.get("cash", None)
        if available is not None:
            available_f = float(available)
            state["coverage"]["available_cash"] = round(available_f, 2)
            state["coverage"]["covered"] = bool(available_f >= buffer_required)
            state["coverage"]["note"] = "computed from capital state"
    except Exception:
        pass

    store.save_reserves(state)

    # optional audit + alert
    try:
        from backend.app.core_gov.audit import service as audit_service  # type: ignore
        audit_service.log({
            "event_type": "system",
            "level": "info",
            "message": "OBLIGATIONS reserve recalculated",
            "actor": "api",
            "ref_type": "obligations_reserve",
            "ref_id": "",
            "meta": {"monthly_required": state["monthly_required"], "buffer_required": state["buffer_required"]},
        })
    except Exception:
        pass

    # if not covered, best-effort alert
    try:
        if state["coverage"]["covered"] is False:
            from backend.app.deals import alerts_store  # type: ignore
            alerts_store.create_alert({
                "title": "OBLIGATIONS NOT COVERED",
                "severity": "high",
                "message": f"Required buffer {state['buffer_required']} not covered by available cash.",
                "meta": {"buffer_required": state["buffer_required"], "available_cash": state["coverage"]["available_cash"]},
            })
    except Exception:
        pass

    return state


def get_reserve_state() -> Dict[str, Any]:
    return store.read_reserves() or {}


def obligations_status(buffer_multiplier: float = 1.25) -> Dict[str, Any]:
    state = recalc_reserve_state(buffer_multiplier=buffer_multiplier)
    covered = state.get("coverage", {}).get("covered", None)
    # cone-safe status
    return {
        "ok": True,
        "covered": covered,
        "monthly_required": state.get("monthly_required"),
        "buffer_required": state.get("buffer_required"),
        "autopay_verified": state.get("autopay_verified"),
        "autopay_total": state.get("autopay_total"),
        "note": state.get("coverage", {}).get("note"),
        "updated_at": state.get("updated_at"),
    }


def autopay_setup_guide(obligation_id: str) -> Dict[str, Any]:
    o = get_obligation(obligation_id)
    if not o:
        raise KeyError("obligation not found")
    ap = o.get("autopay") or {}
    steps = [
        "Log into your bank (desktop is easiest).",
        "Go to: Payments / Bill Payments / Payees (wording varies by bank).",
        f"Add payee that matches: {ap.get('payee') or '[PAYEE NAME NEEDED]'}",
        f"Enter account/reference: {ap.get('reference') or '[ACCOUNT/REFERENCE NEEDED]'}",
        f"Set recurring payment for amount: {o.get('amount')} {o.get('currency')}",
        f"Set schedule to match frequency: {o.get('frequency')} (due day: {o.get('due_day')})",
        "Turn on confirmations / email receipts if available.",
        "Return here and mark verified when completed.",
    ]
    return {
        "obligation_id": obligation_id,
        "name": o.get("name"),
        "amount": o.get("amount"),
        "currency": o.get("currency"),
        "frequency": o.get("frequency"),
        "due_day": o.get("due_day"),
        "autopay": ap,
        "steps": steps,
    }
