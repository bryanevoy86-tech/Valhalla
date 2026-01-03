from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from . import store


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_autopay_proof_pack(obligation_id: str, bank: str = "", include_autopay_plan: bool = True) -> Dict[str, Any]:
    # Best-effort: fetch obligation (may not exist in budget module)
    ob = None
    try:
        from backend.app.core_gov.budget import service as bsvc  # type: ignore
        # Try to get obligations list and find match
        if hasattr(bsvc, 'list_obligations'):
            obs = bsvc.list_obligations()
            ob = next((x for x in obs if x.get("id") == obligation_id), None)
        elif hasattr(bsvc, 'get_obligation'):
            ob = bsvc.get_obligation(obligation_id)
    except Exception:
        pass
    
    if not ob:
        raise KeyError("obligation not found")

    now = _utcnow_iso()
    pid = "pp_" + uuid.uuid4().hex[:12]

    autopay_plan = None
    warnings: List[str] = []
    if include_autopay_plan:
        try:
            from backend.app.core_gov.autopay import service as asvc  # type: ignore
            autopay_plan = asvc.build_autopay_plan(obligation_id=obligation_id, bank=bank, mode="checklist", meta={})
        except Exception as e:
            warnings.append(f"autopay module unavailable: {type(e).__name__}: {e}")
            autopay_plan = None

    checklist = [
        "Screenshot the scheduled payment setup screen (date, amount, payee).",
        "Screenshot the payee/biller details page.",
        "If e-transfer: screenshot the recurring e-transfer setup (or saved contact + reminder rules).",
        "Save confirmation email/PDF if your bank provides it.",
        "Add 1 screenshot showing the account balance buffer (optional but useful).",
    ]

    rec = {
        "id": pid,
        "type": "autopay_proof_pack",
        "obligation_id": obligation_id,
        "obligation_snapshot": ob,
        "bank": (bank or ob.get("account_hint") or "").strip(),
        "checklist": checklist,
        "autopay_plan": autopay_plan or {},
        "attachments": [],   # later: doc_ids or blob_refs
        "warnings": warnings,
        "created_at": now,
    }

    items = store.list_items()
    items.append(rec)
    if len(items) > 400:
        items = items[-400:]
    store.save_items(items)
    return rec


def list_items(obligation_id: str = "") -> List[Dict[str, Any]]:
    items = store.list_items()
    if obligation_id:
        items = [x for x in items if x.get("obligation_id") == obligation_id]
    items.sort(key=lambda x: x.get("created_at",""), reverse=True)
    return items[:200]


def patch_attachments(pack_id: str, attachments: List[Dict[str, Any]]) -> Dict[str, Any]:
    items = store.list_items()
    tgt = None
    for x in items:
        if x.get("id") == pack_id:
            tgt = x
            break
    if not tgt:
        raise KeyError("proof pack not found")
    tgt["attachments"] = attachments or []
    store.save_items(items)
    return tgt
