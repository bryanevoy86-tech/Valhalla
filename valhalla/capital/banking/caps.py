"""
Default caps per tag – conservative & safe
"""

DEFAULT_CAPS = {
    "OPERATING": {
        "per_transfer": 5_000,
        "daily": 15_000,
    },
    "RESERVE": {
        "per_transfer_in": 20_000,
        "per_transfer_out": 2_000,
        "daily": 5_000,
    },
    "TAX": {
        "per_transfer": 10_000,
        "daily": 10_000,
        "scheduled_only": True,
    },
    "TRUST": {
        "manual_only": True,
    },
    "DEAL_STAGING": {
        "per_transfer": 2_000,
        "daily": 4_000,
    },
    "CREDIT": {
        "read_only": True,
    },
}
