from typing import Dict, List, Tuple

from app.core.engines.policy_types import PolicyResult
from app.core.engines.registry import ENGINE_REGISTRY
from app.core.engines.states import EngineState


def evaluate_sequencing_gate(
    engine_name: str,
    target_state: EngineState,
    current_states: Dict[str, EngineState],
) -> PolicyResult:
    blockers: List[str] = []
    warnings: List[str] = []

    if engine_name not in ENGINE_REGISTRY:
        blockers.append(f"Unknown engine: {engine_name}")
        return PolicyResult(ok=False, blockers=blockers, warnings=warnings)

    # Engine layering rule:
    # A higher-layer engine may not promote unless lower-layer engines are at least stable.
    target_layer = ENGINE_REGISTRY[engine_name]["layer"]

    for other_name, meta in ENGINE_REGISTRY.items():
        other_layer = meta["layer"]
        if other_layer < target_layer:
            other_state = current_states.get(other_name, meta["initial_state"])
            # Define "stable" for lower layers: SANDBOX or ACTIVE is acceptable,
            # but DISABLED/DORMANT means foundation isn't even running.
            if other_state in (EngineState.DISABLED, EngineState.DORMANT):
                blockers.append(
                    f"Sequencing blocked: lower-layer engine '{other_name}' "
                    f"is {other_state.value}"
                )

    # Trading advisory special rule: never ACTIVE here (future only)
    if engine_name == "trading_advisory" and target_state == EngineState.ACTIVE:
        blockers.append("trading_advisory cannot be promoted to ACTIVE (future-only)")

    return PolicyResult(ok=(len(blockers) == 0), blockers=blockers, warnings=warnings)
