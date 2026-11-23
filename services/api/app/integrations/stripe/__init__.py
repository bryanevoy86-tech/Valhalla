"""Stripe integration module."""

DISPUTE_LIFECYCLE_EVENTS = frozenset({
    "charge.dispute.updated", "charge.dispute.funds_withdrawn", "charge.dispute.funds_reinstated",
})
DISPUTE_EVENTS = DISPUTE_LIFECYCLE_EVENTS | {"charge.dispute.created", "charge.dispute.closed"}
CHARGE_CORRECTION_EVENTS = DISPUTE_EVENTS | {"charge.refunded"}
ACTIVE_DISPUTE_STATUSES = frozenset({
    "warning_needs_response", "warning_under_review", "needs_response", "under_review",
    "appeal_needs_response", "appeal_under_review",
})
TERMINAL_DISPUTE_STATUSES = frozenset({"won", "lost", "warning_closed"})
