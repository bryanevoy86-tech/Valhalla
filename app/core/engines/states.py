from enum import Enum


class EngineState(str, Enum):
    DISABLED = "DISABLED"
    DORMANT = "DORMANT"
    SANDBOX = "SANDBOX"
    ACTIVE = "ACTIVE"


ENGINE_STATE_ORDER = [
    EngineState.DISABLED,
    EngineState.DORMANT,
    EngineState.SANDBOX,
    EngineState.ACTIVE,
]


def can_transition(current: EngineState, target: EngineState) -> bool:
    try:
        return ENGINE_STATE_ORDER.index(target) == ENGINE_STATE_ORDER.index(current) + 1
    except ValueError:
        return False
