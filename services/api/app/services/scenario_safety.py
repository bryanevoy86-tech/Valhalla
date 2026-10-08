from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ScenarioSafetyInput:
    scenario_id: str
    category: str
    practice_safe: bool
    external_side_effects_allowed: bool
    dataset_id: str | None
    dataset_type: str | None
    source_id: str | None
    source_data_class: str | None
    jurisdiction: str | None
    business_engine: str | None


@dataclass(frozen=True)
class ScenarioSafetyResult:
    safe: bool
    blocking_reasons: list[str] = field(default_factory=list)
    lineage: dict[str, Any] = field(default_factory=dict)


def evaluate_scenario_safety(payload: ScenarioSafetyInput) -> ScenarioSafetyResult:
    reasons: list[str] = []
    category = str(payload.category or "").strip().upper()
    dataset_type = str(payload.dataset_type or "").strip().upper()

    if not payload.practice_safe:
        reasons.append("scenario is not marked practice_safe")

    if payload.external_side_effects_allowed:
        reasons.append("external side effects must be disabled")

    if category == "NORMAL" and dataset_type == "VERIFIED_REAL_OUTCOME":
        reasons.append("verified real outcome dataset cannot be used with NORMAL category")

    if category == "CROSS_BUSINESS" and not str(payload.business_engine or "").strip():
        reasons.append("cross-business scenario requires business_engine")

    if category == "CROSS_JURISDICTION" and not str(payload.jurisdiction or "").strip():
        reasons.append("cross-jurisdiction scenario requires jurisdiction")

    safe = len(reasons) == 0
    return ScenarioSafetyResult(
        safe=safe,
        blocking_reasons=reasons,
        lineage={
            "scenario": {
                "scenario_id": payload.scenario_id,
                "category": payload.category,
            },
            "dataset": {
                "dataset_id": payload.dataset_id,
                "dataset_type": payload.dataset_type,
            },
            "source": {
                "source_id": payload.source_id,
                "source_data_class": payload.source_data_class,
            },
        },
    )
