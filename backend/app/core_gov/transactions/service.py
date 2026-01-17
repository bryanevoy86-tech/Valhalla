from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
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
    return date.fromisoformat(s)


def _month_key(d: date) -> str:
    return f"{d.year:04d}-{d.month:02d}"


def _obligations_covered() -> Optional[bool]:
    # returns True/False/None
    try:
        from backend.app.core_gov.obligations import service as oblig_service  # type: ignore
        st = oblig_service.obligations_status(buffer_multiplier=1.25)
        return st.get("covered")
    except Exception:
        return None


def _budget_touch(bucket_id: str, month: str, delta_spent: float) -> None:
    # update budget snapshot spent/remaining (best-effort; if budget module missing, we still post tx)
    try:
        from backend.app.core_gov.budget import service as budget_service  # type: ignore
        # load month snapshots (creates missing)
        snaps = budget_service.get_month(month=month)
        # modify the one we need
        found = None
        for s in snaps:
            if s.get("bucket_id") == bucket_id:
                found = s
                break
        if not found:
            return

        # snapshots are stored in budget store; easiest is to write direct via budget store map
        from backend.app.core_gov.budget import store as budget_store  # type: ignore
        snap_map = {}
        for s in budget_store.list_snapshots():
            snap_map[f"{s['month']}::{s['bucket_id']}"] = s
        key = f"{month}::{bucket_id}"
        s = snap_map.get(key) or found
        s["spent"] = round(float(s.get("spent") or 0.0) + float(delta_spent or 0.0), 2)
        # remaining recomputed when month endpoint is called (budget_service.get_month)
        s["updated_at"] = _utcnow_iso()
        snap_map[key] = s
        budget_store.save_snapshots(list(snap_map.values()))
    except Exception:
        pass


def create_tx(payload: Dict[str, Any]) -> Dict[str, Any]:
    tx_type = payload.get("tx_type")
    if tx_type not in ("income", "expense"):
        raise ValueError("tx_type must be income/expense")

    try:
        amount = float(payload.get("amount"))
    except Exception:
        raise ValueError("amount must be a number")
    if amount < 0:
        raise ValueError("amount must be >= 0")

    ds = _norm(payload.get("date") or "")
    if not ds:
        raise ValueError("date is required (YYYY-MM-DD)")
    d = _parse_date(ds)
    month = _month_key(d)

    desc = _norm(payload.get("description") or "")
    if not desc:
        raise ValueError("description is required")

    bucket_id = _norm(payload.get("bucket_id") or "")

    # obligations gating: if not covered, block LOW priority discretionary expenses (C/D) unless essentials bucket.
    covered = _obligations_covered()
    priority = payload.get("priority") or "B"
    if tx_type == "expense" and covered is False and priority in ("C", "D"):
        # allow if bucket is essentials (best-effort check)
        allow = False
        if bucket_id:
            try:
                from backend.app.core_gov.budget import service as budget_service  # type: ignore
                b = budget_service.get_bucket(bucket_id)
                if b and b.get("bucket_type") == "essentials":
                    allow = True
            except Exception:
                pass
        if not allow:
            raise ValueError("obligations not covered: discretionary expense blocked (priority C/D). Use essentials or raise priority.")

    now = _utcnow_iso()
    tid = "tx_" + uuid.uuid4().hex[:12]

    rec = {
        "id": tid,
        "tx_type": tx_type,
        "amount": float(amount),
        "currency": _norm(payload.get("currency") or "CAD") or "CAD",
        "date": ds,
        "description": desc,
        "bucket_id": bucket_id,
        "priority": priority,
        "status": payload.get("status") or "posted",
        "merchant": _norm(payload.get("merchant") or ""),
        "category": _norm(payload.get("category") or ""),
        "link_type": _norm(payload.get("link_type") or ""),
        "link_id": _norm(payload.get("link_id") or ""),
        "notes": payload.get("notes") or "",
        "tags": _dedupe(payload.get("tags") or []),
        "meta": payload.get("meta") or {},
        "created_at": now,
        "updated_at": now,
    }

    items = store.list_all()
    items.append(rec)
    store.save_all(items)

    # update budget spent (expense increases spent; income does not touch buckets in v1)
    if tx_type == "expense" and bucket_id and rec["status"] == "posted":
        _budget_touch(bucket_id=bucket_id, month=month, delta_spent=float(amount))

    # best-effort: audit log
    try:
        from backend.app.core_gov.audit import service as audit_service  # type: ignore
        audit_service.log({
            "event_type": "money",
            "level": "info",
            "message": f"TX posted: {tx_type} {amount} {rec['currency']} ({desc})",
            "actor": "api",
            "ref_type": "transaction",
            "ref_id": tid,
            "meta": {"bucket_id": bucket_id, "date": ds, "priority": priority},
        })
    except Exception:
        pass

    return rec


def list_txs(
    tx_type: Optional[str] = None,
    status: Optional[str] = None,
    bucket_id: Optional[str] = None,
    month: Optional[str] = None,
) -> List[Dict[str, Any]]:
    items = store.list_all()
    if tx_type:
        items = [x for x in items if x.get("tx_type") == tx_type]
    if status:
        items = [x for x in items if x.get("status") == status]
    if bucket_id:
        items = [x for x in items if x.get("bucket_id") == bucket_id]
    if month:
        items = [x for x in items if (x.get("date") or "").startswith(month)]
    # newest first
    items.sort(key=lambda x: x.get("date", ""), reverse=True)
    return items


def void_tx(tx_id: str) -> Dict[str, Any]:
    items = store.list_all()
    tgt = None
    for x in items:
        if x["id"] == tx_id:
            tgt = x
            break
    if not tgt:
        raise KeyError("transaction not found")

    if tgt.get("status") == "void":
        return tgt

    tgt["status"] = "void"
    tgt["updated_at"] = _utcnow_iso()
    store.save_all(items)

    # reverse budget spend if it was an expense
    try:
        if tgt.get("tx_type") == "expense" and tgt.get("bucket_id"):
            d = _parse_date(tgt.get("date"))
            month = _month_key(d)
            _budget_touch(bucket_id=tgt["bucket_id"], month=month, delta_spent=-float(tgt.get("amount") or 0.0))
    except Exception:
        pass

    return tgt
