from typing import Dict

from app.core.engines.policy_types import PolicyResult
from app.core.engines.states import EngineState
from app.core.engines.gates_sequencing import evaluate_sequencing_gate
from app.core.engines.gates_survival import evaluate_survival_gate


def merge_results(*results: PolicyResult) -> PolicyResult:
    blockers = []
    warnings = []
    ok = True
    for r in results:
        ok = ok and r.ok
        blockers.extend(r.blockers)
        warnings.extend(r.warnings)
    return PolicyResult(ok=ok, blockers=blockers, warnings=warnings)


def evaluate_transition_policy(
    engine_name: str,
    target_state: EngineState,
    current_states: Dict[str, EngineState],
    # Survival inputs (wire to real metrics later)
    monthly_net_cad: float,
    monthly_burn_cad: float,
    critical_runbook_blockers: int,
) -> PolicyResult:
    # Gate #7 always applies
    seq = evaluate_sequencing_gate(engine_name, target_state, current_states)

    # Gate #1 applies for promotions that increase operational risk
    # (anything moving toward ACTIVE, and sometimes SANDBOX for higher engines)
    if target_state in (EngineState.SANDBOX, EngineState.ACTIVE):
        surv = evaluate_survival_gate(monthly_net_cad, monthly_burn_cad, critical_runbook_blockers)
        return merge_results(seq, surv)

    return seq
