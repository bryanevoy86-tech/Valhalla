from __future__ import annotations
from typing import Any, Dict

def board() -> Dict[str, Any]:
    out: Dict[str, Any] = {}

    # Inbox
    try:
        from backend.app.core_gov.inbox.service import inbox  # type: ignore
        out["inbox"] = inbox(limit=25)
    except Exception:
        out["inbox"] = {}

    # Cashflow
    try:
        from backend.app.core_gov.cashflow.service import forecast  # type: ignore
        out["cashflow_30"] = forecast(days=30)
    except Exception:
        out["cashflow_30"] = {}

    # Sub audit
    try:
        from backend.app.core_gov.subscriptions.audit import audit  # type: ignore
        out["subscriptions_audit"] = audit()
    except Exception:
        out["subscriptions_audit"] = {}

    # Warranty report
    try:
        from backend.app.core_gov.assets.warranty import warranty_report  # type: ignore
        out["warranty_report"] = warranty_report(limit=20)
    except Exception:
        out["warranty_report"] = {}

    # Shopping estimate
    try:
        from backend.app.core_gov.shopping.cost import estimate  # type: ignore
        out["shopping_estimate"] = estimate(status="open")
    except Exception:
        out["shopping_estimate"] = {}

    # Forecast rollup
    try:
        from backend.app.core_gov.forecast.rollup import rollup  # type: ignore
        out["runout_forecast"] = rollup(limit=10, window_days=30)
    except Exception:
        out["runout_forecast"] = {}

    # Payments upcoming
    try:
        from backend.app.core_gov.payments import store as pstore  # type: ignore
        from backend.app.core_gov.payments.service import schedule as psched  # type: ignore
        out["payments_upcoming"] = {"items": psched(pstore.list_items(), days=30)[:50]}
    except Exception:
        out["payments_upcoming"] = {}

    # Payments reconcile
    try:
        from backend.app.core_gov.reconcile.service import reconcile  # type: ignore
        out["payments_reconcile"] = reconcile(days=30)
    except Exception:
        out["payments_reconcile"] = {}

    # Shield Lite
    try:
        from backend.app.core_gov.shield_lite import store as sstore  # type: ignore
        out["shield_lite"] = sstore.get_state()
    except Exception:
        out["shield_lite"] = {}

    return out
