from __future__ import annotations
import importlib
import json
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from sandbox_integrated.engine_profile import EngineCycleResult, EngineProfile
from sandbox_integrated.reporting import write_cycle_report
from sandbox_integrated.resources import ResourceState, allocate_budgets

# Reuse your proven Phase 3 guard (institution-grade)
from security.phase3_guard import assert_phase3_safety


@dataclass
class IntegratedSandboxConfig:
    cycle_seconds: int
    resources: Dict[str, Any]
    engines: List[Dict[str, Any]]


def load_config(path: str) -> IntegratedSandboxConfig:
    raw = json.loads(open(path, "r", encoding="utf-8").read())
    return IntegratedSandboxConfig(
        cycle_seconds=int(raw.get("cycle_seconds", 30)),
        resources=raw.get("resources", {}),
        engines=raw.get("engines", []),
    )


def load_engine(module_path: str) -> EngineProfile:
    mod = importlib.import_module(module_path)
    if not hasattr(mod, "get_engine"):
        raise RuntimeError(f"Engine module {module_path} must expose get_engine()")
    eng = mod.get_engine()
    return eng


def run_integrated(
    *,
    config_path: str = "configs/sandbox_integrated.json",
    out_dir: str = "reports/integrated_sandbox",
    max_cycles: Optional[int] = None
) -> None:
    # Global safety invariants (Phase 3 guard)
    assert_phase3_safety()

    cfg = load_config(config_path)

    rs = ResourceState(
        sim_capital_pool=float(cfg.resources.get("sim_capital_pool", 1000000)),
        max_items_global=int(cfg.resources.get("max_items_per_cycle_global", 200)),
        max_actions_global=int(cfg.resources.get("max_actions_per_cycle_global", 0)),
    )

    engines_cfg = cfg.engines
    engines: Dict[str, EngineProfile] = {}
    for e in engines_cfg:
        if e.get("enabled"):
            engines[str(e["name"])] = load_engine(str(e["module"]))

    if not engines:
        raise RuntimeError("No enabled engines. Set engines[].enabled=true in config.")

    cycle = 0
    while True:
        cycle += 1
        if max_cycles is not None and cycle > max_cycles:
            break

        cycle_id = time.strftime("%Y%m%d_%H%M%S", time.gmtime())

        budgets = allocate_budgets(engines_cfg, rs)
        budgets_dict = [
            {"name": b.name, "budget_pct": b.budget_pct, "max_items": b.max_items, "max_actions": b.max_actions}
            for b in budgets
            if b.name in engines
        ]

        results: List[EngineCycleResult] = []
        total_ingested = total_analyzed = total_intents = 0

        for b in budgets_dict:
            eng = engines[b["name"]]
            res = EngineCycleResult(engine_name=eng.name)

            items = eng.ingest(max_items=int(b["max_items"]))
            res.ingested = len(items)

            analyzed = eng.analyze(items)
            res.analyzed = len(analyzed)

            intents = eng.propose_actions(analyzed, max_actions=int(b["max_actions"]))
            res.intents = len(intents)

            export_meta = eng.export(analyzed, intents)
            res.metrics.update(export_meta or {})

            results.append(res)
            total_ingested += res.ingested
            total_analyzed += res.analyzed
            total_intents += res.intents

        global_metrics = {
            "sim_capital_pool": rs.sim_capital_pool,
            "total_ingested": total_ingested,
            "total_analyzed": total_analyzed,
            "total_intents": total_intents,
            "cycle_seconds": cfg.cycle_seconds
        }

        write_cycle_report(
            out_dir=out_dir,
            cycle_id=cycle_id,
            budgets=budgets_dict,
            results=results,
            global_metrics=global_metrics
        )

        time.sleep(cfg.cycle_seconds)
