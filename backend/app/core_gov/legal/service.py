from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from . import store


def _utcnow():
    return datetime.now(timezone.utc)


def _norm(s: str) -> str:
    return (s or "").strip()


def create_profile(country: str, region: str, name: str, notes: str = "") -> Dict[str, Any]:
    profiles = store.list_profiles()
    now = _utcnow()
    rec = {
        "id": "jur_" + uuid.uuid4().hex[:12],
        "country": (country or "").upper(),
        "region": (region or "").upper(),
        "name": _norm(name),
        "notes": _norm(notes),
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }
    profiles.append(rec)
    store.save_profiles(profiles)
    return rec


def get_profile(profile_id: str) -> Optional[Dict[str, Any]]:
    for p in store.list_profiles():
        if p["id"] == profile_id:
            return p
    return None


def list_profiles_filtered(country: Optional[str] = None, region: Optional[str] = None) -> List[Dict[str, Any]]:
    profiles = store.list_profiles()
    if country:
        country = country.upper()
        profiles = [p for p in profiles if p["country"] == country]
    if region:
        region = region.upper()
        profiles = [p for p in profiles if p["region"] == region]
    return profiles


def create_rule(name: str, description: str, country: str, region: str, severity: str, conditions: List[Dict[str, Any]], action_hint: str = "") -> Dict[str, Any]:
    rules = store.list_rules()
    now = _utcnow()
    rec = {
        "id": "lr_" + uuid.uuid4().hex[:12],
        "name": _norm(name),
        "description": _norm(description),
        "country": (country or "").upper(),
        "region": (region or "").upper(),
        "severity": (severity or "info").lower(),
        "conditions": conditions or [],
        "action_hint": _norm(action_hint),
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }
    rules.append(rec)
    store.save_rules(rules)
    return rec


def get_rule(rule_id: str) -> Optional[Dict[str, Any]]:
    for r in store.list_rules():
        if r["id"] == rule_id:
            return r
    return None


def list_rules_filtered(country: Optional[str] = None, region: Optional[str] = None) -> List[Dict[str, Any]]:
    rules = store.list_rules()
    if country:
        country = country.upper()
        rules = [r for r in rules if r["country"] == country]
    if region:
        region = region.upper()
        rules = [r for r in rules if r["region"] == region]
    return rules


def _cond_ok(context: Dict[str, Any], condition: Dict[str, Any]) -> bool:
    field = condition.get("field", "")
    op = condition.get("op", "eq")
    value = condition.get("value")

    val = context.get(field)

    if op == "exists":
        return val is not None
    elif op == "truthy":
        return bool(val)
    elif op == "falsy":
        return not bool(val)
    elif op == "eq":
        return val == value
    elif op == "neq":
        return val != value
    elif op == "in":
        return val in (value or [])
    elif op == "nin":
        return val not in (value or [])
    elif op == "contains":
        if isinstance(val, (list, str)):
            return value in val
        return False
    return False


def normalize_context(context: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(context)
    # normalize province -> region
    if "province" in out and "region" not in out:
        out["region"] = out["province"]
    # uppercase country/region
    if "country" in out and isinstance(out["country"], str):
        out["country"] = out["country"].upper()
    if "region" in out and isinstance(out["region"], str):
        out["region"] = out["region"].upper()
    return out


def evaluate(context: Dict[str, Any], country: Optional[str] = None, region: Optional[str] = None) -> Dict[str, Any]:
    ctx = normalize_context(context)

    # infer location if not provided
    if not country:
        country = ctx.get("country", "CA")
    if not region:
        region = ctx.get("region", "ON")

    country = (country or "").upper()
    region = (region or "").upper()

    # apply rules
    applicable = list_rules_filtered(country=country, region=region)
    flags = []
    has_block = False

    for rule in applicable:
        conds = rule.get("conditions", [])
        ok = all(_cond_ok(ctx, c) for c in conds)
        if ok:
            flag = {
                "rule_id": rule["id"],
                "name": rule.get("name"),
                "severity": rule.get("severity", "info"),
                "reason": f"Rule '{rule.get('name')}' triggered",
                "action_hint": rule.get("action_hint", ""),
            }
            flags.append(flag)
            if rule.get("severity") == "block":
                has_block = True

    summary = ""
    if has_block:
        summary = "BLOCKED: One or more block-severity rules triggered."
    elif flags:
        summary = f"Caution: {len(flags)} rule(s) triggered."
    else:
        summary = "Clear: No rules triggered."

    return {
        "ok": True,
        "country": country,
        "region": region,
        "flags": flags,
        "blocked": has_block,
        "summary": summary,
    }
