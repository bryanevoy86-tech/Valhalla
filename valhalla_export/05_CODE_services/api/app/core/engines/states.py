from __future__ import annotations

from enum import Enum


class EngineState(str, Enum):
    DISABLED = "DISABLED"
    DORMANT = "DORMANT"
    SANDBOX = "SANDBOX"
    ACTIVE = "ACTIVE"


_ALLOWED_TRANSITIONS: dict[EngineState, set[EngineState]] = {
    EngineState.DISABLED: {EngineState.DORMANT},
    EngineState.DORMANT: {EngineState.SANDBOX},
    EngineState.SANDBOX: {EngineState.ACTIVE, EngineState.DORMANT},
    EngineState.ACTIVE: {EngineState.SANDBOX},  # step-down only
}


def allowed_next_states(current: EngineState) -> list[EngineState]:
    return sorted(_ALLOWED_TRANSITIONS.get(current, set()), key=lambda s: s.value)


def assert_transition(current: EngineState, target: EngineState) -> None:
    if target not in _ALLOWED_TRANSITIONS.get(current, set()):
        raise ValueError(f"Invalid transition: {current} -> {target}")
