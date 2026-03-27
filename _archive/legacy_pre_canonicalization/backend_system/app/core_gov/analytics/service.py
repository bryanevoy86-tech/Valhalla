from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from . import store


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_count(loader) -> Tuple[int, str | None]:
    try:
        n = loader()
        return int(n), None
    except Exception as e:
        return 0, str(e)


def snapshot() -> Dict[str, Any]:
    warnings: List[str] = []
    metrics: Dict[str, Any] = {}

    # Deals
    try:
        from backend.app.deals import store as deals_store  # type: ignore
        deals = deals_store.list_deals()
        metrics["deals.count"] = len(deals)
    except Exception as e:
        metrics["deals.count"] = 0
        warnings.append(f"deals unavailable: {e}")

    # Followups
    try:
        from backend.app.deals import followups_store  # type: ignore
        fu = followups_store.list_followups()
        metrics["followups.count"] = len(fu)
    except Exception as e:
        metrics["followups.count"] = 0
        warnings.append(f"followups unavailable: {e}")

    # Buyers
    try:
        from backend.app.deals import buyers_store  # type: ignore
        buyers = buyers_store.list_buyers()
        metrics["buyers.count"] = len(buyers)
    except Exception as e:
        metrics["buyers.count"] = 0
        warnings.append(f"buyers unavailable: {e}")

    # Core gov modules (use stores directly when possible)
    try:
        from backend.app.core_gov.grants import store as grants_store  # type: ignore
        metrics["grants.count"] = len(grants_store.list_grants())  # expect your grants store
    except Exception as e:
        metrics["grants.count"] = 0
        warnings.append(f"grants unavailable: {e}")

    try:
        from backend.app.core_gov.loans import store as loans_store  # type: ignore
        metrics["loans.count"] = len(loans_store.list_loans())  # expect your loans store
    except Exception as e:
        metrics["loans.count"] = 0
        warnings.append(f"loans unavailable: {e}")

    try:
        from backend.app.core_gov.docs import store as docs_store  # type: ignore
        idx = docs_store.read_index()
        metrics["vault.docs"] = len(idx.get("items", []))
    except Exception as e:
        metrics["vault.docs"] = 0
        warnings.append(f"vault unavailable: {e}")

    try:
        from backend.app.core_gov.know import store as know_store  # type: ignore
        metrics["know.docs"] = len(know_store.list_docs())
        metrics["know.chunks"] = len(know_store.list_chunks())
    except Exception as e:
        metrics["know.docs"] = 0
        metrics["know.chunks"] = 0
        warnings.append(f"know unavailable: {e}")

    try:
        from backend.app.core_gov.legal import store as legal_store  # type: ignore
        metrics["legal.rules"] = len(legal_store.list_rules())
        metrics["legal.profiles"] = len(legal_store.list_profiles())
    except Exception as e:
        metrics["legal.rules"] = 0
        metrics["legal.profiles"] = 0
        warnings.append(f"legal unavailable: {e}")

    try:
        from backend.app.core_gov.comms import store as comms_store  # type: ignore
        metrics["comms.drafts"] = len(comms_store.list_drafts())
        metrics["comms.sendlog"] = len(comms_store.list_sendlog())
    except Exception as e:
        metrics["comms.drafts"] = 0
        metrics["comms.sendlog"] = 0
        warnings.append(f"comms unavailable: {e}")

    try:
        from backend.app.core_gov.jv import store as jv_store  # type: ignore
        metrics["jv.partners"] = len(jv_store.list_partners())
        metrics["jv.links"] = len(jv_store.list_links())
    except Exception as e:
        metrics["jv.partners"] = 0
        metrics["jv.links"] = 0
        warnings.append(f"jv unavailable: {e}")

    try:
        from backend.app.core_gov.property import store as prop_store  # type: ignore
        metrics["property.count"] = len(prop_store.list_properties())
    except Exception as e:
        metrics["property.count"] = 0
        warnings.append(f"property unavailable: {e}")

    try:
        from backend.app.core_gov.credit import store as credit_store  # type: ignore
        metrics["credit.vendors"] = len(credit_store.list_vendors())
        metrics["credit.tasks"] = len(credit_store.list_tasks())
        metrics["credit.scores"] = len(credit_store.list_scores())
        metrics["credit.profile_set"] = 1 if credit_store.get_profile() else 0
    except Exception as e:
        metrics["credit.vendors"] = 0
        metrics["credit.tasks"] = 0
        metrics["credit.scores"] = 0
        metrics["credit.profile_set"] = 0
        warnings.append(f"credit unavailable: {e}")

    snap = {
        "id": "snap_" + uuid.uuid4().hex[:12],
        "created_at": _utcnow_iso(),
        "metrics": metrics,
        "warnings": warnings,
    }
    return snap


def snapshot_and_store() -> Dict[str, Any]:
    snap = snapshot()
    store.append_snapshot(snap)
    return snap


def list_history(limit: int = 50) -> List[Dict[str, Any]]:
    items = store.read_history()
    return list(reversed(items))[: max(1, min(limit, 500))]
