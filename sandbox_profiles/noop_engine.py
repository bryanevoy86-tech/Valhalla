from __future__ import annotations
from typing import Dict, List

from sandbox_integrated.engine_profile import EngineItem, EngineActionIntent


class NoopEngine:
    name = "noop_secondary"

    def ingest(self, *, max_items: int) -> List[EngineItem]:
        return []

    def analyze(self, items: List[EngineItem]) -> List[EngineItem]:
        return items

    def propose_actions(self, items: List[EngineItem], *, max_actions: int) -> List[EngineActionIntent]:
        return []

    def export(self, items: List[EngineItem], intents: List[EngineActionIntent]) -> Dict:
        return {"exported_items": len(items), "exported_intents": len(intents)}

    def cost_model(self) -> Dict:
        return {"cpu_hint": 0.01, "capital_hint": 0}


def get_engine() -> NoopEngine:
    return NoopEngine()
