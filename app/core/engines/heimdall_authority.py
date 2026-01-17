from typing import Dict

from app.core.engines.errors import EngineTransitionDenied
from app.core.engines.registry import ENGINE_REGISTRY
from app.core.engines.states import EngineState, can_transition
from app.core.engines.state_store import EngineStateStore


class HeimdallEngineAuthority:
    """
    Sole authority to transition engine states.
    No engine can self-promote.
    No skipping states.
    """

    def __init__(self, store: EngineStateStore):
        self.store = store

    def get_all_states(self) -> Dict[str, str]:
        snap = self.store.load()
        return {k: v.value for k, v in snap.states.items()}

    def get_state(self, engine_name: str) -> EngineState:
        if engine_name not in ENGINE_REGISTRY:
            raise EngineTransitionDenied(f"Unknown engine: {engine_name}")
        return self.store.get_state(engine_name)

    def transition(self, engine_name: str, target: EngineState) -> EngineState:
        if engine_name not in ENGINE_REGISTRY:
            raise EngineTransitionDenied(f"Unknown engine: {engine_name}")

        current = self.store.get_state(engine_name)

        # Only allow step-by-step transitions
        if not can_transition(current, target):
            raise EngineTransitionDenied(
                f"Invalid transition {engine_name}: {current.value} -> {target.value} "
                f"(no skipping states)"
            )

        self.store.set_state(engine_name, target)
        return target
