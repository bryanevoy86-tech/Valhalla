from app.core.engines.states import EngineState
from app.core.engines.registry import ENGINE_REGISTRY


class EngineBlocked(Exception):
    pass


def engine_guard(
    engine_name: str,
    current_state: EngineState,
    requires_real_world_effect: bool = False,
):
    if engine_name not in ENGINE_REGISTRY:
        raise EngineBlocked(f"Unknown engine: {engine_name}")

    if current_state == EngineState.DISABLED:
        raise EngineBlocked(f"{engine_name} is DISABLED")

    if current_state == EngineState.DORMANT:
        raise EngineBlocked(f"{engine_name} is DORMANT")

    if (
        current_state == EngineState.SANDBOX
        and requires_real_world_effect
    ):
        raise EngineBlocked(
            f"{engine_name} is in SANDBOX — real-world effects blocked"
        )

    return True
