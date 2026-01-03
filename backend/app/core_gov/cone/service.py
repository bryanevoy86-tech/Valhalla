"""Cone service - projection band enforcement with persistence and audit."""
from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Dict

from ..audit.audit_log import audit
from ..canon.canon import ConeBand, EngineClass, get_engine_spec
from ..storage.json_store import read_json, write_json
from .models import ConeDecision, ConeState

CONE_STATE_PATH = Path("data") / "cone_state.json"

_DEFAULT = ConeState(
    band=ConeBand.B_CAUTION,
    reason="Boot default: caution until governance KPIs are green",
    updated_at_utc=dt.datetime.utcnow().isoformat() + "Z",
    metrics={},
)

_ALLOWED_MATRIX: Dict[ConeBand, Dict[EngineClass, set[str]]] = {
    ConeBand.A_EXPANSION: {
        EngineClass.BORING: {"run", "scale"},
        EngineClass.ALPHA: {"run", "scale", "optimize"},
        EngineClass.OPPORTUNISTIC: {"run", "optimize"},
        EngineClass.STANDBY: set(),
        EngineClass.LEGACY: set(),
    },
    ConeBand.B_CAUTION: {
        EngineClass.BORING: {"run"},
        EngineClass.ALPHA: {"run", "optimize"},
        EngineClass.OPPORTUNISTIC: {"run"},
        EngineClass.STANDBY: set(),
        EngineClass.LEGACY: set(),
    },
    ConeBand.C_STABILIZE: {
        EngineClass.BORING: {"run"},
        EngineClass.ALPHA: {"run"},
        EngineClass.OPPORTUNISTIC: set(),
        EngineClass.STANDBY: set(),
        EngineClass.LEGACY: set(),
    },
    ConeBand.D_SURVIVAL: {
        EngineClass.BORING: {"run"},
        EngineClass.ALPHA: set(),
        EngineClass.OPPORTUNISTIC: set(),
        EngineClass.STANDBY: set(),
        EngineClass.LEGACY: set(),
    },
}

_CONE_STATE: ConeState | None = None


def _load_from_disk() -> ConeState:
    """Load cone state from disk, fallback to default if missing or corrupted."""
    raw = read_json(CONE_STATE_PATH)
    if not raw:
        return _DEFAULT
    try:
        return ConeState.model_validate(raw)
    except Exception:
        # If file is corrupted, fall back safely.
        return _DEFAULT


def _persist(state: ConeState) -> None:
    """Write cone state to disk for durability across restarts."""
    write_json(CONE_STATE_PATH, state.model_dump())


def get_cone_state() -> ConeState:
    """Get current cone state, loading from disk on first call."""
    global _CONE_STATE
    if _CONE_STATE is None:
        _CONE_STATE = _load_from_disk()
    return _CONE_STATE


def set_cone_state(band: ConeBand, reason: str, metrics: dict | None = None) -> ConeState:
    """Set cone band and persist to disk with audit trail."""
    global _CONE_STATE
    state = get_cone_state()
    state.band = band
    state.reason = reason
    state.updated_at_utc = dt.datetime.utcnow().isoformat() + "Z"
    state.metrics = metrics or {}

    _persist(state)
    audit("CONE_SET", {"band": band, "reason": reason, "metrics": state.metrics})
    _CONE_STATE = state
    return state


def decide(engine_name: str, action: str) -> ConeDecision:
    """Decide if engine+action is allowed by Cone matrix."""
    spec = get_engine_spec(engine_name)
    state = get_cone_state()
    band = state.band

    allowed_actions = _ALLOWED_MATRIX[band][spec.engine_class]
    if action not in allowed_actions:
        d = ConeDecision(
            allowed=False,
            band=band,
            engine=engine_name,
            action=action,
            reason=f"Denied by Cone: band={band} class={spec.engine_class}",
        )
        audit("CONE_DENY", d.model_dump())
        return d

    if spec.engine_class == EngineClass.BORING and action == "optimize":
        d = ConeDecision(
            allowed=False,
            band=band,
            engine=engine_name,
            action=action,
            reason="Denied: boring engines are SOP-only (no optimize).",
        )
        audit("CONE_DENY", d.model_dump())
        return d

    if spec.engine_class == EngineClass.OPPORTUNISTIC and action == "scale":
        d = ConeDecision(
            allowed=False,
            band=band,
            engine=engine_name,
            action=action,
            reason="Denied: opportunistic engines cannot scale (capped).",
        )
        audit("CONE_DENY", d.model_dump())
        return d

    d = ConeDecision(
        allowed=True, band=band, engine=engine_name, action=action, reason="Allowed by Cone"
    )
    audit("CONE_ALLOW", d.model_dump())
    return d
