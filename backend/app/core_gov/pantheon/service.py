from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from . import store


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_state() -> Dict[str, Any]:
    return store.read_state()


def set_mode(mode: str, reason: str = "", by: str = "api") -> Dict[str, Any]:
    if mode not in ("explore", "execute"):
        raise ValueError("mode must be explore or execute")
    st = store.read_state()
    st["mode"] = mode
    st["reason"] = reason or ""
    st["last_set_at"] = _utcnow_iso()
    st["last_set_by"] = by
    store.write_state(st)
    return st


def _cone_allowed(desired_band: str) -> Tuple[bool, str, List[str]]:
    """
    Optional: consult cone decide endpoint if available. If not, default allow in explore, conservative in execute.
    Returns (allowed, band, warnings)
    """
    warnings: List[str] = []
    st = store.read_state()
    mode = st.get("mode", "explore")

    # If cone module is importable, use it; otherwise local fallback.
    try:
        from backend.app.core_gov.cone import service as cone_service  # type: ignore
        # Expectation: decide returns {"allowed": bool, "band": "A|B|C|D", ...}
        d = cone_service.decide({"requested_band": desired_band})
        return bool(d.get("allowed", True)), (d.get("band") or desired_band), warnings
    except Exception:
        warnings.append("cone decide not available; using local mode-based fallback")

    if mode == "explore":
        return True, desired_band, warnings
    # execute mode: be stricter for D
    if desired_band == "D":
        return False, desired_band, warnings
    return True, desired_band, warnings


def dispatch(intent: str, payload: Dict[str, Any], desired_band: str) -> Dict[str, Any]:
    st = store.read_state()
    mode = st.get("mode", "explore")

    allowed, band, warnings = _cone_allowed(desired_band)

    # routing suggestions (v1 stub)
    intent_l = (intent or "").strip().lower()
    route = "/core/command/what_now"
    suggestion = "Start with /core/command/what_now"

    if "grant" in intent_l:
        route = "/core/grants"
        suggestion = "Use Grants registry and create proof pack + deadline followup"
    elif "loan" in intent_l or "fund" in intent_l:
        route = "/core/loans/recommend_next"
        suggestion = "Run loan recommender and underwriting checklist"
    elif "credit" in intent_l:
        route = "/core/credit/recommend"
        suggestion = "Run credit recommend and build vendor/task plan"
    elif "deal" in intent_l:
        route = "/deals/summary"
        suggestion = "Check deal summary and next action"
    elif "doc" in intent_l or "vault" in intent_l:
        route = "/core/docs"
        suggestion = "Upload and tag docs in the vault"
    elif "know" in intent_l or "ingest" in intent_l:
        route = "/core/know/ingest_inbox"
        suggestion = "Ingest inbox and run search/retrieve"

    # mode-safe messaging
    if mode == "explore":
        suggestion = "[EXPLORE] " + suggestion
    else:
        suggestion = "[EXECUTE] " + suggestion

    return {
        "ok": True,
        "mode": mode,
        "allowed": bool(allowed),
        "band": band,
        "route": route,
        "suggestion": suggestion,
        "warnings": warnings,
    }
