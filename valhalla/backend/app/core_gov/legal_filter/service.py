from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from . import store


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _norm(s: str) -> str:
    return (s or "").strip()


def _get_path(payload: Dict[str, Any], dotted: str) -> Any:
    """
    dotted path: "seller.occupancy" -> payload["seller"]["occupancy"]
    returns None if missing
    """
    cur: Any = payload
    for part in dotted.split("."):
        if not isinstance(cur, dict):
            return None
        if part not in cur:
            return None
        cur = cur.get(part)
    return cur


def upsert_profile(data: Dict[str, Any]) -> Dict[str, Any]:
    key = _norm(data.get("key") or "")
    if not key or ":" not in key:
        raise ValueError("key required, format like CA:MB or US:FL")

    now = _utcnow_iso()
    items = store.list_profiles()
    existing = None
    for p in items:
        if p.get("key") == key:
            existing = p
            break

    if not existing:
        existing = {
            "key": key,
            "name": _norm(data.get("name") or ""),
            "rules": data.get("rules") or [],
            "meta": data.get("meta") or {},
            "created_at": now,
            "updated_at": now,
        }
        items.append(existing)
    else:
        if "name" in data:
            existing["name"] = _norm(data.get("name") or "")
        if "rules" in data:
            existing["rules"] = data.get("rules") or []
        if "meta" in data:
            existing["meta"] = data.get("meta") or {}
        existing["updated_at"] = now

    store.save_profiles(items)
    return existing


def list_profiles() -> List[Dict[str, Any]]:
    items = store.list_profiles()
    items.sort(key=lambda x: x.get("key",""))
    return items


def get_profile(key: str) -> Optional[Dict[str, Any]]:
    key = _norm(key)
    for p in store.list_profiles():
        if p.get("key") == key:
            return p
    return None


def seed_defaults_if_empty() -> Dict[str, Any]:
    items = store.list_profiles()
    if items:
        return {"seeded": False, "count": len(items)}

    # v1 conservative starter rules: simple policy checks + documentation prompts
    defaults = [
        {
            "key": "CA:MB",
            "name": "Manitoba",
            "rules": [
                {
                    "id": "mb_assignment_disclosure",
                    "when": {"field": "strategy", "op": "in", "value": ["wholesale", "assignment"]},
                    "outcome": "flagged",
                    "severity": "medium",
                    "message": "Assignment/wholesale strategy: ensure disclosure language and compliant paperwork is used.",
                    "next_actions": [
                        "Use Valhalla offer templates with assignment disclosure.",
                        "Confirm advertising rules + representation wording.",
                    ],
                },
                {
                    "id": "mb_unknown_entity",
                    "when": {"field": "buyer.entity_type", "op": "eq", "value": ""},
                    "outcome": "flagged",
                    "severity": "low",
                    "message": "Buyer entity type missing: confirm personal vs corporation/trust.",
                    "next_actions": ["Set buyer.entity_type in deal/contact data."],
                },
                {
                    "id": "mb_missing_id_verification",
                    "when": {"field": "seller.id_verified", "op": "eq", "value": False},
                    "outcome": "flagged",
                    "severity": "medium",
                    "message": "Seller ID not verified: risk of fraud / unenforceable agreement.",
                    "next_actions": ["Verify seller identity before signing final offer."],
                },
            ],
            "meta": {"version": 1},
        },
        {
            "key": "US:FL",
            "name": "Florida",
            "rules": [
                {
                    "id": "fl_assignment_attention",
                    "when": {"field": "strategy", "op": "in", "value": ["wholesale", "assignment"]},
                    "outcome": "flagged",
                    "severity": "medium",
                    "message": "FL wholesale: confirm contract assignability + local practice requirements.",
                    "next_actions": ["Use Florida-specific templates and verify assignability clause."],
                },
                {
                    "id": "fl_missing_disclosures",
                    "when": {"field": "disclosures.complete", "op": "eq", "value": False},
                    "outcome": "flagged",
                    "severity": "low",
                    "message": "Disclosures not marked complete: verify required disclosures for transaction type.",
                    "next_actions": ["Mark disclosures.complete=true once validated."],
                },
            ],
            "meta": {"version": 1},
        },
    ]

    now = _utcnow_iso()
    out = []
    for d in defaults:
        out.append({
            "key": d["key"],
            "name": d.get("name",""),
            "rules": d.get("rules") or [],
            "meta": d.get("meta") or {},
            "created_at": now,
            "updated_at": now,
        })

    store.save_profiles(out)
    return {"seeded": True, "count": len(out)}


def _eval_rule(rule: Dict[str, Any], payload: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """
    rule.when = { field, op, value }
    ops: eq, ne, in, nin, gt, gte, lt, lte, exists, missing, contains
    """
    w = rule.get("when") or {}
    field = _norm(w.get("field") or "")
    op = w.get("op") or "eq"
    val = w.get("value")

    actual = _get_path(payload, field) if field else None

    ok = False
    if op == "eq":
        ok = actual == val
    elif op == "ne":
        ok = actual != val
    elif op == "in":
        ok = actual in (val or [])
    elif op == "nin":
        ok = actual not in (val or [])
    elif op == "gt":
        ok = actual is not None and actual > val
    elif op == "gte":
        ok = actual is not None and actual >= val
    elif op == "lt":
        ok = actual is not None and actual < val
    elif op == "lte":
        ok = actual is not None and actual <= val
    elif op == "exists":
        ok = actual is not None
    elif op == "missing":
        ok = actual is None or actual == "" or actual == []
    elif op == "contains":
        ok = isinstance(actual, (list, str)) and (val in actual)
    else:
        ok = False

    evidence = {"field": field, "op": op, "expected": val, "actual": actual}
    return ok, evidence


def run_check(jurisdiction_key: str, subject: str, payload: Dict[str, Any], mode: str = "execute", cone_band: str = "B") -> Dict[str, Any]:
    prof = get_profile(jurisdiction_key)
    if not prof:
        raise KeyError("jurisdiction profile not found")

    findings: List[Dict[str, Any]] = []
    next_actions: List[str] = []
    overall = "allowed"

    for rule in (prof.get("rules") or []):
        triggered, evidence = _eval_rule(rule, payload)
        if not triggered:
            continue

        outcome = rule.get("outcome") or "flagged"
        severity = rule.get("severity") or "low"
        msg = rule.get("message") or "Legal rule triggered"
        rid = rule.get("id") or "rule"

        f = {
            "rule_id": rid,
            "outcome": outcome,
            "severity": severity,
            "message": msg,
            "evidence": evidence,
            "next_actions": rule.get("next_actions") or [],
        }
        findings.append(f)
        next_actions.extend(f["next_actions"])

        if outcome == "blocked":
            overall = "blocked"
        elif outcome == "flagged" and overall != "blocked":
            overall = "flagged"

    # mode-safe: in explore, never block — downgrade blocked->flagged (you can still choose to stop)
    if (mode or "execute") == "explore" and overall == "blocked":
        overall = "flagged"
        next_actions.insert(0, "Explore mode: blocked findings downgraded to flagged (no hard stops).")

    # cone-safe hint only (no enforcement here)
    if cone_band in ("C", "D") and overall in ("flagged", "blocked"):
        next_actions.insert(0, "Cone hint: This action is C/D and has legal risk flags — keep to A/B until cleared.")

    # de-dupe next actions
    na2, seen = [], set()
    for a in next_actions:
        a2 = _norm(a)
        if a2 and a2 not in seen:
            seen.add(a2)
            na2.append(a2)

    return {
        "jurisdiction_key": jurisdiction_key,
        "subject": subject,
        "overall": overall,
        "findings": findings,
        "next_actions": na2,
        "meta": {"profile_name": prof.get("name",""), "mode": mode, "cone_band": cone_band},
    }
