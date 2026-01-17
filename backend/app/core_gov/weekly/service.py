from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Tuple


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _today_iso() -> str:
    return date.today().isoformat()


def _safe_get(fn, default):
    try:
        return fn()
    except Exception:
        return default


def _add_followup(title: str, due_days: int, priority: str, meta: Dict[str, Any]) -> bool:
    try:
        from backend.app.deals import followups_store  # type: ignore
        followups_store.create_followup({
            "title": title,
            "due_date": (date.today() + timedelta(days=due_days)).isoformat(),
            "priority": priority,
            "status": "open",
            "meta": meta,
        })
        return True
    except Exception:
        return False


def _add_alert(title: str, severity: str, message: str, meta: Dict[str, Any]) -> bool:
    try:
        from backend.app.deals import alerts_store  # type: ignore
        alerts_store.create_alert({
            "title": title,
            "severity": severity,
            "message": message,
            "meta": meta,
        })
        return True
    except Exception:
        return False


def run_weekly(create_followups: bool = True) -> Dict[str, Any]:
    findings: List[Dict[str, Any]] = []
    followups_created = 0
    alerts_created = 0

    # 1) Obligations coverage
    covered = None
    buffer_required = None
    try:
        from backend.app.core_gov.obligations import service as oblig_service  # type: ignore
        st = oblig_service.obligations_status(buffer_multiplier=1.25)
        covered = st.get("covered")
        buffer_required = st.get("buffer_required")
        if covered is False:
            findings.append({
                "code": "OBLIGATIONS_NOT_COVERED",
                "severity": "critical",
                "message": f"Household obligations buffer not covered (required ~{buffer_required}).",
                "action_hint": "Add cash buffer, reduce discretionary spend, or raise income. Keep Cone tight until covered.",
                "meta": {"buffer_required": buffer_required},
            })
            if create_followups:
                if _add_followup("Fix: Household obligations buffer not covered", 1, "A", {"buffer_required": buffer_required}):
                    followups_created += 1
            if _add_alert("OBLIGATIONS NOT COVERED", "high", "Obligations buffer not covered. Cone should restrict discretionary actions.", {"buffer_required": buffer_required}):
                alerts_created += 1
        elif covered is None:
            findings.append({
                "code": "OBLIGATIONS_COVERAGE_UNKNOWN",
                "severity": "medium",
                "message": "Obligations coverage unknown (capital cash not available).",
                "action_hint": "Add/confirm capital cash balance key (personal_cash) or keep manual buffer tracking.",
                "meta": {},
            })
    except Exception as e:
        findings.append({
            "code": "OBLIGATIONS_CHECK_FAILED",
            "severity": "medium",
            "message": f"Could not evaluate obligations status: {repr(e)}",
            "action_hint": "Confirm /core/obligations/status endpoint working.",
            "meta": {},
        })

    # 2) Upcoming obligations (next 30)
    try:
        from backend.app.core_gov.obligations import service as oblig_service  # type: ignore
        items = oblig_service.generate_upcoming(_today_iso(), (date.today() + timedelta(days=30)).isoformat())
        unverified = [x for x in items if x.get("autopay_enabled") and not x.get("autopay_verified")]
        if len(unverified) > 0:
            findings.append({
                "code": "AUTOPAY_UNVERIFIED_UPCOMING",
                "severity": "high",
                "message": f"{len(unverified)} upcoming obligations have autopay enabled but not verified.",
                "action_hint": "Run /core/obligations/{id}/autopay_guide then verify autopay.",
                "meta": {"count": len(unverified)},
            })
            if create_followups:
                if _add_followup("Verify autopay for upcoming obligations", 2, "A", {"count": len(unverified)}):
                    followups_created += 1
    except Exception:
        pass

    # 3) Open followups backlog
    try:
        from backend.app.deals import followups_store  # type: ignore
        q = followups_store.list_followups()
        open_items = [x for x in q if x.get("status") == "open"]
        if len(open_items) >= 25:
            findings.append({
                "code": "FOLLOWUPS_BACKLOG",
                "severity": "medium",
                "message": f"Followups backlog is high ({len(open_items)} open).",
                "action_hint": "Run Jarvis weekly_review + clear/close low value followups.",
                "meta": {"open": len(open_items)},
            })
    except Exception:
        pass

    # 4) Shopping list stuck
    try:
        from backend.app.core_gov.flow import service as flow_service  # type: ignore
        sh = flow_service.list_shopping(status="open")
        if len(sh) >= 30:
            findings.append({
                "code": "SHOPPING_BACKLOG",
                "severity": "low",
                "message": f"Shopping list is large ({len(sh)} open).",
                "action_hint": "Bundle items into one run or cancel duplicates.",
                "meta": {"open": len(sh)},
            })
    except Exception:
        pass

    # 5) Replacement plans due soon (ready/planned)
    try:
        from backend.app.core_gov.replacements import service as rep_service  # type: ignore
        reps = rep_service.list_replacements(status="planned")
        if len(reps) >= 10:
            findings.append({
                "code": "REPLACEMENTS_PILEUP",
                "severity": "low",
                "message": f"Many planned replacements ({len(reps)}).",
                "action_hint": "Reprioritize: keep only top 3 active; archive the rest.",
                "meta": {"planned": len(reps)},
            })
    except Exception:
        pass

    ok = not any(f["severity"] in ("high", "critical") for f in findings)

    # optional audit log
    try:
        from backend.app.core_gov.audit import service as audit_service  # type: ignore
        audit_service.log({
            "event_type": "system",
            "level": "info" if ok else "warn",
            "message": f"WEEKLY check complete: ok={ok}, findings={len(findings)}",
            "actor": "api",
            "ref_type": "weekly_check",
            "ref_id": "",
            "meta": {"ok": ok, "findings": len(findings)},
        })
    except Exception:
        pass

    return {
        "ok": ok,
        "generated_at": _utcnow_iso(),
        "findings": findings,
        "created_followups": followups_created,
        "created_alerts": alerts_created,
    }
