from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass
class EngineBudget:
    name: str
    budget_pct: float
    max_items: int
    max_actions: int


@dataclass
class ResourceState:
    sim_capital_pool: float
    max_items_global: int
    max_actions_global: int


def allocate_budgets(
    engines: List[Dict],
    resource_state: ResourceState
) -> List[EngineBudget]:
    """
    Simple, stable allocator:
    - each enabled engine gets its configured min_budget_pct
    - remaining is distributed proportionally by min_budget_pct (same order)
    This avoids an engine hijacking the whole system.
    """
    enabled = [e for e in engines if e.get("enabled")]
    if not enabled:
        return []

    min_sum = sum(float(e.get("min_budget_pct", 0.0)) for e in enabled)
    # If min_sum is 0 or >1, normalize safely
    if min_sum <= 0:
        for e in enabled:
            e["min_budget_pct"] = 1.0 / len(enabled)
        min_sum = 1.0
    if min_sum > 1.0:
        for e in enabled:
            e["min_budget_pct"] = float(e.get("min_budget_pct", 0.0)) / min_sum
        min_sum = 1.0

    # Remaining budget (if any) distributed by the same weights (stable)
    remaining = 1.0 - min_sum
    weights = [float(e.get("min_budget_pct", 0.0)) for e in enabled]
    wsum = sum(weights) or 1.0

    budgets: List[EngineBudget] = []
    for e, w in zip(enabled, weights):
        extra = remaining * (w / wsum)
        pct = float(e.get("min_budget_pct", 0.0)) + extra

        budgets.append(
            EngineBudget(
                name=str(e["name"]),
                budget_pct=pct,
                max_items=int(e.get("max_items_per_cycle", 50)),
                max_actions=int(e.get("max_actions_per_cycle", 0))
            )
        )

    # Enforce globals by proportional scaling (items + actions)
    total_items = sum(b.max_items for b in budgets)
    if total_items > resource_state.max_items_global:
        scale = resource_state.max_items_global / max(total_items, 1)
        for b in budgets:
            b.max_items = max(1, int(b.max_items * scale))

    total_actions = sum(b.max_actions for b in budgets)
    if total_actions > resource_state.max_actions_global:
        scale = resource_state.max_actions_global / max(total_actions, 1)
        for b in budgets:
            b.max_actions = int(b.max_actions * scale)

    return budgets
