from __future__ import annotations
import json
import time
from pathlib import Path
from typing import Any, Dict, List

from sandbox_integrated.engine_profile import EngineCycleResult


def write_cycle_report(
    *,
    out_dir: str,
    cycle_id: str,
    budgets: List[Dict[str, Any]],
    results: List[EngineCycleResult],
    global_metrics: Dict[str, Any]
) -> str:
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    payload = {
        "cycle_id": cycle_id,
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "budgets": budgets,
        "results": [r.__dict__ for r in results],
        "global_metrics": global_metrics,
    }
    out_path = Path(out_dir) / f"INTEGRATED_{cycle_id}.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return str(out_path)
