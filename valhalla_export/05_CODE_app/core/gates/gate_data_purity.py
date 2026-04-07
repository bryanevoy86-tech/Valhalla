from app.core.engines.policy_types import PolicyResult


def evaluate_data_purity_gate(
    quarantine_backlog: int,
    clean_promotion_enabled: bool,
) -> PolicyResult:
    blockers = []
    warnings = []

    if not clean_promotion_enabled:
        blockers.append("Data purity gate: clean promotion disabled (clean_promotion_enabled=false)")

    # Backlog isn't always a blocker; it becomes one if it grows uncontrolled.
    if quarantine_backlog > 500:
        blockers.append(f"Data purity gate: quarantine backlog too high ({quarantine_backlog})")
    elif quarantine_backlog > 100:
        warnings.append(f"Quarantine backlog elevated ({quarantine_backlog})")

    return PolicyResult(ok=(len(blockers) == 0), blockers=blockers, warnings=warnings)
