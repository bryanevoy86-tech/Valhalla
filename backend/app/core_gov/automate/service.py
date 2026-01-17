from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from . import store


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _norm(s: str) -> str:
    return (s or "").strip()


def create_rule(payload: Dict[str, Any]) -> Dict[str, Any]:
    name = _norm(payload.get("name") or "")
    if not name:
        raise ValueError("name is required")
    trig = payload.get("trigger")
    act = payload.get("action")
    if not trig or not act:
        raise ValueError("trigger and action are required")

    now = _utcnow_iso()
    rid = "rl_" + uuid.uuid4().hex[:12]
    rec = {
        "id": rid,
        "name": name,
        "status": payload.get("status") or "active",
        "trigger": trig,
        "threshold": float(payload.get("threshold") or 0.0),
        "action": act,
        "action_payload": payload.get("action_payload") or {},
        "tags": payload.get("tags") or [],
        "meta": payload.get("meta") or {},
        "created_at": now,
        "updated_at": now,
    }
    items = store.list_rules()
    items.append(rec)
    store.save_rules(items)
    return rec


def list_rules(status: Optional[str] = None, trigger: Optional[str] = None) -> List[Dict[str, Any]]:
    items = store.list_rules()
    if status:
        items = [x for x in items if x.get("status") == status]
    if trigger:
        items = [x for x in items if x.get("trigger") == trigger]
    return items


def _metric_obligations_not_covered() -> Tuple[bool, Dict[str, Any]]:
    try:
        from backend.app.core_gov.obligations import service as oblig_service  # type: ignore
        st = oblig_service.obligations_status(buffer_multiplier=1.25)
        covered = st.get("covered")
        return (covered is False), {"covered": covered, "buffer_required": st.get("buffer_required")}
    except Exception as e:
        return False, {"error": repr(e)}


def _metric_shopping_backlog_over(threshold: float) -> Tuple[bool, Dict[str, Any]]:
    try:
        from backend.app.core_gov.flow import service as flow_service  # type: ignore
        open_items = flow_service.list_shopping(status="open")
        return (len(open_items) > int(threshold)), {"open": len(open_items), "threshold": threshold}
    except Exception as e:
        return False, {"error": repr(e)}


def _metric_followups_backlog_over(threshold: float) -> Tuple[bool, Dict[str, Any]]:
    try:
        from backend.app.deals import followups_store  # type: ignore
        q = followups_store.list_followups()
        open_items = [x for x in q if x.get("status") == "open"]
        return (len(open_items) > int(threshold)), {"open": len(open_items), "threshold": threshold}
    except Exception as e:
        return False, {"error": repr(e)}


def _metric_autopay_unverified_over(threshold: float) -> Tuple[bool, Dict[str, Any]]:
    try:
        from backend.app.core_gov.obligations import service as oblig_service  # type: ignore
        items = oblig_service.generate_upcoming(date.today().isoformat(), (date.today() + timedelta(days=30)).isoformat())
        unverified = [x for x in items if x.get("autopay_enabled") and not x.get("autopay_verified")]
        return (len(unverified) > int(threshold)), {"unverified": len(unverified), "threshold": threshold}
    except Exception as e:
        return False, {"error": repr(e)}


def _execute_action(rule: Dict[str, Any], context: Dict[str, Any]) -> Tuple[bool, str]:
    act = rule.get("action")
    payload = rule.get("action_payload") or {}

    if act == "create_followup":
        try:
            from backend.app.deals import followups_store  # type: ignore
            title = payload.get("title") or f"AUTO: {rule.get('name')}"
            due_days = int(payload.get("due_days") or 1)
            priority = payload.get("priority") or "B"
            followups_store.create_followup({
                "title": title,
                "due_date": (date.today() + timedelta(days=due_days)).isoformat(),
                "priority": priority,
                "status": "open",
                "meta": {"rule_id": rule.get("id"), "trigger": rule.get("trigger"), "context": context},
            })
            return True, "followup_created"
        except Exception as e:
            return False, f"followup_failed:{repr(e)}"

    if act == "create_alert":
        try:
            from backend.app.deals import alerts_store  # type: ignore
            title = payload.get("title") or f"AUTO: {rule.get('name')}"
            severity = payload.get("severity") or "medium"
            message = payload.get("message") or "Automation triggered."
            alerts_store.create_alert({
                "title": title,
                "severity": severity,
                "message": message,
                "meta": {"rule_id": rule.get("id"), "trigger": rule.get("trigger"), "context": context},
            })
            return True, "alert_created"
        except Exception as e:
            return False, f"alert_failed:{repr(e)}"

    return False, "unknown_action"


def evaluate(run_actions: bool = True) -> Dict[str, Any]:
    rules = [r for r in store.list_rules() if r.get("status") == "active"]
    results: List[Dict[str, Any]] = []
    triggered = 0
    actions_executed = 0

    for r in rules:
        trig = r.get("trigger")
        thr = float(r.get("threshold") or 0.0)

        hit = False
        ctx: Dict[str, Any] = {"threshold": thr}

        if trig == "obligations_not_covered":
            hit, ctx2 = _metric_obligations_not_covered()
            ctx.update(ctx2)
        elif trig == "shopping_backlog_over":
            hit, ctx2 = _metric_shopping_backlog_over(thr)
            ctx.update(ctx2)
        elif trig == "followups_backlog_over":
            hit, ctx2 = _metric_followups_backlog_over(thr)
            ctx.update(ctx2)
        elif trig == "autopay_unverified_over":
            hit, ctx2 = _metric_autopay_unverified_over(thr)
            ctx.update(ctx2)
        else:
            results.append({"rule_id": r.get("id"), "rule": r.get("name"), "ok": False, "error": "unknown_trigger"})
            continue

        if hit:
            triggered += 1
            if run_actions:
                ok, msg = _execute_action(r, ctx)
                results.append({"rule_id": r.get("id"), "rule": r.get("name"), "triggered": True, "action_ok": ok, "action": msg, "context": ctx})
                if ok:
                    actions_executed += 1
            else:
                results.append({"rule_id": r.get("id"), "rule": r.get("name"), "triggered": True, "action_ok": None, "context": ctx})
        else:
            results.append({"rule_id": r.get("id"), "rule": r.get("name"), "triggered": False, "context": ctx})

    ok = True
    return {"ok": ok, "triggered": triggered, "actions_executed": actions_executed, "results": results}
