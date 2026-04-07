from __future__ import annotations

import json
from datetime import datetime, time
from typing import Dict, Any, Optional, Tuple, List

from sqlalchemy.orm import Session
from app.models.market_policy import MarketPolicy


PROVINCES = {"BC","AB","SK","MB","ON","QC","NB","NS","PE","NL","YT","NT","NU"}


def _parse_hhmm(s: str) -> time:
    hh, mm = s.split(":")
    return time(int(hh), int(mm))


def upsert_policy(db: Session, province: str, market: str, enabled: bool, rules: Dict[str, Any], changed_by: str, reason: str | None) -> MarketPolicy:
    province = province.strip().upper()
    market = market.strip().upper()
    if province not in PROVINCES:
        raise ValueError(f"Invalid province: {province}")

    row = db.query(MarketPolicy).filter(MarketPolicy.province == province, MarketPolicy.market == market).first()
    if not row:
        row = MarketPolicy(province=province, market=market, rules_json="{}")
        db.add(row)

    row.enabled = bool(enabled)
    row.rules_json = json.dumps(rules)
    row.changed_by = changed_by
    row.reason = reason
    row.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(row)
    return row


def get_effective_policy(db: Session, province: str, market: str | None) -> Tuple[Optional[MarketPolicy], Dict[str, Any]]:
    """
    Returns best match: province+market, else province+ALL, else None.
    """
    province = province.strip().upper()
    market_u = (market or "ALL").strip().upper()

    row = db.query(MarketPolicy).filter(MarketPolicy.province == province, MarketPolicy.market == market_u).first()
    if not row:
        row = db.query(MarketPolicy).filter(MarketPolicy.province == province, MarketPolicy.market == "ALL").first()
    if not row:
        return None, {}

    rules = json.loads(row.rules_json or "{}")
    return row, rules


def is_contact_allowed(rules: Dict[str, Any], local_weekday: int, local_hhmm: str, channel: str) -> Tuple[bool, str]:
    """
    local_weekday: 0=Mon..6=Sun
    local_hhmm: "HH:MM"
    """
    channel = channel.strip().upper()
    allowed_channels = [c.upper() for c in rules.get("channels_allowed", ["SMS","CALL","EMAIL"])]
    if channel not in allowed_channels:
        return False, f"channel_not_allowed({channel})"

    windows: List[Dict[str, Any]] = rules.get("contact_windows_local", [])
    if not windows:
        return True, "no_windows_defined"

    now_t = _parse_hhmm(local_hhmm)
    for w in windows:
        days = w.get("days", [])
        if days and local_weekday not in days:
            continue
        start = _parse_hhmm(w["start"])
        end = _parse_hhmm(w["end"])
        if start <= now_t <= end:
            return True, "within_window"
    return False, "outside_contact_window"
