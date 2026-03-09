"""
P-SCHED-1: Scheduler state store.

Manages scheduler state including last tick timestamp.
"""
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional

STATE_FILE = "backend/data/scheduler_state.json"

DEFAULT_STATE = {
    "last_tick": None,
    "next_tick": None,
    "tick_interval_seconds": 3600,
    "enabled": True
}


def _ensure_file() -> None:
    """Ensure state file exists."""
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    if not os.path.exists(STATE_FILE):
        with open(STATE_FILE, "w") as f:
            json.dump(DEFAULT_STATE.copy(), f, indent=2)


def get_state() -> Dict[str, Any]:
    """
    Get scheduler state.
    
    Returns:
        State dict with last_tick, next_tick, tick_interval_seconds, enabled
    """
    _ensure_file()
    with open(STATE_FILE, "r") as f:
        return json.load(f)


def set_last_tick(ts: str) -> Dict[str, Any]:
    """
    Set last tick timestamp.
    
    Args:
        ts: ISO format timestamp
    
    Returns:
        Updated state dict
    """
    _ensure_file()
    
    with open(STATE_FILE, "r") as f:
        state = json.load(f)
    
    state["last_tick"] = ts
    
    # Calculate next tick
    try:
        interval = state.get("tick_interval_seconds", 3600)
        dt = datetime.fromisoformat(ts)
        next_dt = dt.timestamp() + interval
        state["next_tick"] = datetime.fromtimestamp(next_dt).isoformat()
    except Exception:
        pass
    
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)
    
    return state
