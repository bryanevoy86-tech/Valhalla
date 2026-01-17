import json
import os
from dataclasses import dataclass
from typing import Dict, Optional

from app.core.engines.states import EngineState
from app.core.engines.registry import ENGINE_REGISTRY


DEFAULT_STATE_FILE = os.environ.get(
    "ENGINE_STATE_FILE",
    os.path.join(os.getcwd(), "var", "engine_states.json"),
)


@dataclass
class EngineStateSnapshot:
    states: Dict[str, EngineState]
    version: int = 1


class EngineStateStore:
    """
    Minimal persistent store for engine states.
    - File-backed for simplicity and portability.
    - Fail-closed behavior:
        If file missing/corrupt -> initialize to registry defaults.
    """

    def __init__(self, path: str = DEFAULT_STATE_FILE):
        self.path = path

    def _ensure_dir(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)

    def load(self) -> EngineStateSnapshot:
        # Defaults from registry
        defaults = {
            name: meta["initial_state"]
            for name, meta in ENGINE_REGISTRY.items()
        }

        if not os.path.exists(self.path):
            return EngineStateSnapshot(states=defaults, version=1)

        try:
            with open(self.path, "r", encoding="utf-8") as f:
                raw = json.load(f) or {}
            raw_states = raw.get("states", {}) or {}
            version = int(raw.get("version", 1))

            merged: Dict[str, EngineState] = {}
            for name, default_state in defaults.items():
                val = raw_states.get(name, default_state)
                merged[name] = EngineState(val) if not isinstance(val, EngineState) else val

            return EngineStateSnapshot(states=merged, version=version)
        except Exception:
            # Fail-closed: revert to defaults
            return EngineStateSnapshot(states=defaults, version=1)

    def save(self, snapshot: EngineStateSnapshot) -> None:
        self._ensure_dir()
        payload = {
            "version": snapshot.version,
            "states": {k: v.value for k, v in snapshot.states.items()},
        }
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        os.replace(tmp, self.path)

    def get_state(self, engine_name: str) -> EngineState:
        snap = self.load()
        return snap.states.get(engine_name, EngineState.DISABLED)

    def set_state(self, engine_name: str, state: EngineState) -> None:
        snap = self.load()
        snap.states[engine_name] = state
        self.save(snap)
