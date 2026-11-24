"""Translate verified rehearsal observations to operating review blockers."""


def checkout_operating_blockers(observations: list[dict]) -> set[str]:
    blockers = set()
    for row in observations:
        if not isinstance(row, dict):
            blockers.add("CHECKOUT_EVIDENCE_CONFLICT")
            continue
        status = row.get("status")
        if status == "EVIDENCE_CONFLICT" or row.get("verified_commercial_revenue") is not False:
            blockers.add("CHECKOUT_EVIDENCE_CONFLICT")
            continue
        if status == "UNRECONCILED_FIXTURE":
            blockers.add("CHECKOUT_FIXTURE_UNRECONCILED")
        contribution = row.get("fixture_contribution_minor")
        if type(contribution) is int and contribution < 0:
            blockers.add("NEGATIVE_FIXTURE_CONTRIBUTION")
        exception = row.get("fulfillment_exception")
        if isinstance(exception, dict) and exception.get("status") == "HELD":
            blockers.add("CHECKOUT_FULFILLMENT_HELD")
        if row.get("owner_followup_required") is True and row.get("refunded_minor", 0):
            blockers.add("CHECKOUT_REFUND_REVIEW_REQUIRED")
    return blockers
