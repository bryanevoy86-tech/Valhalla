"""
Engine activation rules - defines readiness criteria for each engine.
"""

ENGINE_RULES = {
    "wholesaling": {
        "min_samples": 20,
        "max_fp_rate": 0.10,  # 10% false positive rate max
        "min_approval_rate": 0.75,  # 75% approval rate min
        "required_days_stable": 7,
    },
    "trading_advisory": {
        "min_samples": 50,
        "max_drawdown": 0.05,  # 5% max drawdown
        "required_days_stable": 14,
    },
    "arbitrage": {
        "min_samples": 30,
        "min_roi": 0.03,  # 3% minimum ROI
        "required_days_stable": 3,
    },
}

# Promotion order - do not violate
PROMOTION_ORDER = [
    "wholesaling",  # Must prove itself first
    "arbitrage",  # Can follow quickly
    "trading_advisory",  # Last due to complexity
]
