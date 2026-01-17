from typing import Dict

from app.core.engines.errors import EngineTransitionDenied
from app.core.engines.heimdall_runtime import heimdall_engine_authority
from app.core.engines.policy_engine import evaluate_transition_policy
from app.core.engines.registry import ENGINE_REGISTRY
from app.core.engines.states import EngineState


def _current_states_as_enum() -> Dict[str, EngineState]:
    raw = heimdall_engine_authority.get_all_states()
    out: Dict[str, EngineState] = {}
    for name, meta in ENGINE_REGISTRY.items():
        out[name] = EngineState(raw.get(name, meta["initial_state"].value))
    return out


def request_transition(
    engine_name: str,
    target_state: EngineState,
    *,
    monthly_net_cad: float = 0.0,
    monthly_burn_cad: float = 200.0,  # safe default; wire later
    critical_runbook_blockers: int = 0,
) -> Dict:
    current_states = _current_states_as_enum()

    policy = evaluate_transition_policy(
        engine_name=engine_name,
        target_state=target_state,
        current_states=current_states,
        monthly_net_cad=monthly_net_cad,
        monthly_burn_cad=monthly_burn_cad,
        critical_runbook_blockers=critical_runbook_blockers,
    )

    if not policy.ok:
        raise EngineTransitionDenied("; ".join(policy.blockers))

    new_state = heimdall_engine_authority.transition(engine_name, target_state)
    return {
        "engine": engine_name,
        "new_state": new_state.value,
        "policy": policy.to_dict(),
    }
