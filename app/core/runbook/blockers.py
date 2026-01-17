from typing import Dict, List

from app.core.engines.registry import ENGINE_REGISTRY
from app.core.engines.states import EngineState
from app.core.engines.heimdall_runtime import heimdall_engine_authority
from app.core.engines.policy_types import PolicyResult
from app.core.engines.gates_survival import evaluate_survival_gate
from app.core.gates.gate_learning import evaluate_closed_loop_learning_gate
from app.core.gates.gate_data_purity import evaluate_data_purity_gate
from app.core.metrics.runtime import metrics_store
from app.core.data_intake.quarantine_store import QuarantineStore


def _engine_states_as_enum() -> Dict[str, EngineState]:
    raw = heimdall_engine_authority.get_all_states()
    out: Dict[str, EngineState] = {}
    for name, meta in ENGINE_REGISTRY.items():
        out[name] = EngineState(raw.get(name, meta["initial_state"].value))
    return out


def _merge(results: List[PolicyResult]) -> PolicyResult:
    blockers: List[str] = []
    warnings: List[str] = []
    ok = True
    for r in results:
        ok = ok and r.ok
        blockers.extend(r.blockers)
        warnings.extend(r.warnings)
    return PolicyResult(ok=ok, blockers=blockers, warnings=warnings)


def evaluate_core_blockers() -> Dict:
    """
    Used by runbook to report BLOCKERS without 500s.
    This does not transition anything; it only reports.
    """
    m = metrics_store.load()
    quarantine = QuarantineStore()
    quarantine_backlog = quarantine.count_by_status("QUARANTINE")

    # Gate #1 (Survival)
    g1 = evaluate_survival_gate(
        monthly_net_cad=m.monthly_net_cad,
        monthly_burn_cad=m.monthly_burn_cad,
        critical_runbook_blockers=m.critical_runbook_blockers,
    )

    # Gate #2 (Closed-loop learning)
    g2 = evaluate_closed_loop_learning_gate(
        outcomes_required_ratio=m.outcomes_required_ratio,
        outcomes_recorded_ratio=m.outcomes_recorded_ratio,
    )

    # Gate #3 (Data purity)
    g3 = evaluate_data_purity_gate(
        quarantine_backlog=quarantine_backlog,
        clean_promotion_enabled=m.clean_promotion_enabled,
    )

    merged = _merge([g1, g2, g3])

    return {
        "ok": merged.ok,
        "blockers": merged.blockers,
        "warnings": merged.warnings,
        "metrics": {
            "monthly_net_cad": m.monthly_net_cad,
            "monthly_burn_cad": m.monthly_burn_cad,
            "critical_runbook_blockers": m.critical_runbook_blockers,
            "outcomes_required_ratio": m.outcomes_required_ratio,
            "outcomes_recorded_ratio": m.outcomes_recorded_ratio,
            "quarantine_backlog": quarantine_backlog,
            "clean_promotion_enabled": m.clean_promotion_enabled,
        },
        "engine_states": {k: v.value for k, v in _engine_states_as_enum().items()},
    }
