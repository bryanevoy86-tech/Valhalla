from app.core.engines.policy_types import PolicyResult


def evaluate_survival_gate(
    monthly_net_cad: float,
    monthly_burn_cad: float,
    critical_runbook_blockers: int,
) -> PolicyResult:
    blockers = []
    warnings = []

    if critical_runbook_blockers > 0:
        blockers.append(f"{critical_runbook_blockers} critical runbook blockers present")

    if monthly_burn_cad <= 0:
        blockers.append("monthly_burn_cad must be > 0")

    if monthly_net_cad < monthly_burn_cad:
        blockers.append(
            f"Survival not proven: monthly_net_cad ({monthly_net_cad:.2f}) < "
            f"monthly_burn_cad ({monthly_burn_cad:.2f})"
        )

    return PolicyResult(ok=(len(blockers) == 0), blockers=blockers, warnings=warnings)
