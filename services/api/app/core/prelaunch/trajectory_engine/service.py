"""Trajectory Engine Service Layer"""
from .schemas import CurrentTrajectory, ScenarioRequest, ScenarioResult, TrajectoryPoint


def get_current_trajectory() -> CurrentTrajectory:
    """
    Get current financial trajectory.
    
    Placeholder → later replaced by real financial model integration
    pulling from arbitrage_guard, brrrr_stability, and EIA guardian engines.
    """
    points = [
        TrajectoryPoint(
            month=i,
            cashflow=2000 + i * 150,
            net_worth=50000 + i * 3000,
            risk_level="GREEN",
        )
        for i in range(1, 13)
    ]
    return CurrentTrajectory(months=points)


def simulate_scenario(payload: ScenarioRequest) -> ScenarioResult:
    """
    Simulate a "what if" scenario based on deal count, bankroll, and expense changes.
    
    Later integrates with real financial + risk modeling.
    """
    base = get_current_trajectory()

    notes = [
        "Scenario simulation uses placeholder logic.",
        "Real financial + risk engine logic will be plugged in later.",
    ]

    adjusted_points = []
    for p in base.months:
        new_cashflow = p.cashflow + payload.additional_deals * 300
        new_cashflow += payload.bankroll_change * 0.05
        new_cashflow -= payload.expense_change

        adjusted_points.append(
            TrajectoryPoint(
                month=p.month,
                cashflow=new_cashflow,
                net_worth=p.net_worth + payload.additional_deals * 1500,
                risk_level="GREEN",
            )
        )

    return ScenarioResult(
        months=adjusted_points,
        confidence=0.7,
        notes=notes,
    )
