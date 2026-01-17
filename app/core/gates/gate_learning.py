from app.core.engines.policy_types import PolicyResult


def evaluate_closed_loop_learning_gate(
    outcomes_required_ratio: float,
    outcomes_recorded_ratio: float,
) -> PolicyResult:
    blockers = []
    warnings = []

    if outcomes_required_ratio <= 0:
        warnings.append("outcomes_required_ratio <= 0; learning gate effectively disabled")
        return PolicyResult(ok=True, blockers=[], warnings=warnings)

    if outcomes_recorded_ratio < outcomes_required_ratio:
        blockers.append(
            f"Closed-loop learning incomplete: outcomes_recorded_ratio "
            f"({outcomes_recorded_ratio:.2f}) < required ({outcomes_required_ratio:.2f})"
        )

    return PolicyResult(ok=(len(blockers) == 0), blockers=blockers, warnings=warnings)
