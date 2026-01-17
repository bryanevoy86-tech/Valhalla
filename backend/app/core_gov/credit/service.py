from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from . import store


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _norm(s: str) -> str:
    return (s or "").strip()


def upsert_profile(payload: Dict[str, Any]) -> Dict[str, Any]:
    profile = store.get_profile() or {}
    for k in ["business_name","country","province","incorporation_date","ein_bn","address","phone","website","email"]:
        if k in payload and payload.get(k) is not None:
            profile[k] = _norm(payload.get(k) or "")
    profile["meta"] = payload.get("meta") or profile.get("meta") or {}
    profile["updated_at"] = _utcnow_iso()
    store.save_profile(profile)
    return profile


def _util(balance: float, limit: float) -> float:
    if limit <= 0:
        return 0.0
    return round((balance / limit) * 100.0, 2)


def create_account(payload: Dict[str, Any]) -> Dict[str, Any]:
    name = _norm(payload.get("name") or "")
    if not name:
        raise ValueError("name is required")

    now = _utcnow_iso()
    cid = "cr_" + uuid.uuid4().hex[:12]

    limit = float(payload.get("credit_limit") or 0.0)
    bal = float(payload.get("balance") or 0.0)

    rec = {
        "id": cid,
        "name": name,
        "account_type": payload.get("account_type") or "credit_card",
        "status": payload.get("status") or "active",
        "bureau_reporting": payload.get("bureau_reporting") or [],
        "opened_date": _norm(payload.get("opened_date") or ""),
        "credit_limit": limit,
        "balance": bal,
        "utilization": _util(bal, limit),
        "due_day": int(payload.get("due_day") or 1),
        "autopay": bool(payload.get("autopay", False)),
        "notes": payload.get("notes") or "",
        "tags": payload.get("tags") or [],
        "meta": payload.get("meta") or {},
        "created_at": now,
        "updated_at": now,
    }

    items = store.list_accounts()
    items.append(rec)
    store.save_accounts(items)
    return rec


def list_accounts(status: Optional[str] = None, account_type: Optional[str] = None) -> List[Dict[str, Any]]:
    items = store.list_accounts()
    if status:
        items = [x for x in items if x.get("status") == status]
    if account_type:
        items = [x for x in items if x.get("account_type") == account_type]
    return items


def get_account(account_id: str) -> Optional[Dict[str, Any]]:
    for x in store.list_accounts():
        if x["id"] == account_id:
            return x
    return None


def update_utilization(account_id: str, balance: float, credit_limit: Optional[float] = None) -> Dict[str, Any]:
    items = store.list_accounts()
    tgt = None
    for x in items:
        if x["id"] == account_id:
            tgt = x
            break
    if not tgt:
        raise KeyError("account not found")

    tgt["balance"] = float(balance or 0.0)
    if credit_limit is not None:
        tgt["credit_limit"] = float(credit_limit or 0.0)
    tgt["utilization"] = _util(float(tgt.get("balance") or 0.0), float(tgt.get("credit_limit") or 0.0))
    tgt["updated_at"] = _utcnow_iso()
    store.save_accounts(items)

    try:
        if tgt["utilization"] >= 30.0:
            from backend.app.deals import alerts_store, followups_store  # type: ignore
            alerts_store.create_alert({
                "title": "CREDIT UTILIZATION HIGH",
                "severity": "medium" if tgt["utilization"] < 50 else "high",
                "message": f"{tgt['name']} utilization is {tgt['utilization']}%. Aim < 30%.",
                "meta": {"account_id": account_id, "utilization": tgt["utilization"]},
            })
            followups_store.create_followup({
                "title": f"Lower utilization: {tgt['name']} ({tgt['utilization']}%)",
                "due_date": (date.today() + timedelta(days=3)).isoformat(),
                "priority": "B",
                "status": "open",
                "meta": {"account_id": account_id, "target": "<30%"},
            })
    except Exception:
        pass

    return tgt


def totals() -> Dict[str, Any]:
    items = store.list_accounts()
    total_limit = sum(float(x.get("credit_limit") or 0.0) for x in items if x.get("status") == "active")
    total_bal = sum(float(x.get("balance") or 0.0) for x in items if x.get("status") == "active")
    util = _util(total_bal, total_limit)
    return {"total_limit": round(total_limit, 2), "total_balance": round(total_bal, 2), "total_utilization": util}


def recommend_next_steps() -> List[str]:
    t = totals()
    steps = [
        "Ensure business info is consistent across bank/bureaus (name/address/phone).",
        "Open 1–2 vendor tradelines (Net-30) that report, then pay early.",
        "Keep utilization under 30% (under 10% is ideal if achievable).",
        "Never miss a payment; autopay minimums where possible.",
        "After 90+ days of reporting, apply for a business card/LOC aligned to revenue.",
    ]
    if t["total_utilization"] >= 30:
        steps.insert(0, "Immediate: pay down balances to get utilization under 30%.")
    if t["total_limit"] <= 0:
        steps.insert(0, "Start: add your first business credit account/tradeline to track here.")
    return steps


def add_task(title: str, due_date: str, priority: str = "B", meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if not title:
        raise ValueError("title required")
    if not due_date:
        raise ValueError("due_date required (YYYY-MM-DD)")

    now = _utcnow_iso()
    tid = "ct_" + uuid.uuid4().hex[:12]
    rec = {
        "id": tid,
        "title": title,
        "due_date": due_date,
        "priority": priority,
        "status": "open",
        "meta": meta or {},
        "created_at": now,
        "updated_at": now,
    }
    items = store.list_tasks()
    items.append(rec)
    store.save_tasks(items)
    return rec


def list_tasks(status: Optional[str] = None) -> List[Dict[str, Any]]:
    items = store.list_tasks()
    if status:
        items = [x for x in items if x.get("status") == status]
    items.sort(key=lambda x: x.get("due_date", ""))
    return items
