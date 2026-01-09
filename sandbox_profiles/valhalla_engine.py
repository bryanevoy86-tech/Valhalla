from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Dict, List

from sandbox_integrated.engine_profile import EngineItem, EngineActionIntent


class ValhallaCoreEngine:
    name = "valhalla_core"

    def __init__(self) -> None:
        self.real_dir = Path(os.getenv("VALHALLA_REAL_LEADS_DIR", "data/inbox/real_leads"))

    def ingest(self, *, max_items: int) -> List[EngineItem]:
        # Minimal, safe ingest: read filenames and create items.
        # If you have a proper ingest function, you can swap it in later without changing orchestration.
        items: List[EngineItem] = []
        if not self.real_dir.exists():
            return items

        files = sorted([p for p in self.real_dir.iterdir() if p.is_file()])[:max_items]
        for p in files:
            items.append(EngineItem(item_id=str(p.name), payload={"path": str(p)}))
        return items

    def analyze(self, items: List[EngineItem]) -> List[EngineItem]:
        # Placeholder analysis hook. The real system already scores inside SANDBOX_ACTIVATION.
        # Integrated sandbox focuses on interaction/resource effects first.
        return items

    def propose_actions(self, items: List[EngineItem], *, max_actions: int) -> List[EngineActionIntent]:
        # Phase 3 integrated sandbox never proposes real actions (max_actions will be 0 by config)
        return []

    def export(self, items: List[EngineItem], intents: List[EngineActionIntent]) -> Dict:
        # Writes a small artifact proving the engine participated this cycle (no sensitive data).
        out_dir = Path("reports/integrated_sandbox/engine_exports")
        out_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "engine": self.name,
            "items_seen": len(items),
            "intents": len(intents)
        }
        out_path = out_dir / "valhalla_core_last.json"
        out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return {"engine_export_path": str(out_path), "items_seen": len(items)}

    def cost_model(self) -> Dict:
        return {"cpu_hint": 1.0, "capital_hint": 0}


def get_engine() -> ValhallaCoreEngine:
    return ValhallaCoreEngine()
