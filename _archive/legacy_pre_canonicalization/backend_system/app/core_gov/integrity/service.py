from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Tuple

DATA_ROOT = os.path.join("backend", "data")


def _check_json_file(path: str) -> Tuple[bool, str]:
    if not os.path.exists(path):
        return False, "missing"
    try:
        with open(path, "r", encoding="utf-8") as f:
            json.load(f)
        return True, "ok"
    except Exception as e:
        return False, f"invalid_json: {e}"


def run_checks() -> Dict[str, Any]:
    # Core files you expect to exist (add as you want)
    expected = [
        os.path.join("backend", "data", "deals.json"),
        os.path.join("backend", "data", "buyers.json"),
        os.path.join("backend", "data", "followups.json"),
        os.path.join("backend", "data", "jobs.json"),
        os.path.join("backend", "data", "alerts.json"),
        os.path.join("backend", "data", "config.json"),
        os.path.join("backend", "data", "capital.json"),
        # gov modules
        os.path.join("backend", "data", "grants", "grants.json"),
        os.path.join("backend", "data", "loans", "loans.json"),
    ]

    results: List[Dict[str, Any]] = []
    passed = 0
    failed = 0

    for p in expected:
        ok, note = _check_json_file(p)
        results.append({"check": "json_file", "path": p, "ok": ok, "note": note})
        passed += 1 if ok else 0
        failed += 0 if ok else 1

    # lightweight directory scan: ensure no .tmp left behind
    tmp_left = []
    for root, _, files in os.walk(DATA_ROOT):
        for fn in files:
            if fn.endswith(".tmp"):
                tmp_left.append(os.path.join(root, fn))
    if tmp_left:
        results.append({"check": "tmp_files", "ok": False, "note": "tmp files found", "paths": tmp_left[:50]})
        failed += 1
    else:
        results.append({"check": "tmp_files", "ok": True, "note": "none" })
        passed += 1

    checks_run = len(results)
    return {"ok": failed == 0, "checks_run": checks_run, "passed": passed, "failed": failed, "results": results}
