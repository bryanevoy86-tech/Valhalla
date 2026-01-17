from __future__ import annotations

import argparse
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "ops" / "capabilities" / "registry.json"

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def load_registry() -> dict[str, Any]:
    if not REGISTRY.exists():
        raise SystemExit(f"[ERR] Registry not found: {REGISTRY}")
    return json.loads(REGISTRY.read_text(encoding="utf-8"))

def is_certified(cap: dict[str, Any]) -> bool:
    # Accept either status= CERTIFIED or certification.certified = true
    status_ok = str(cap.get("status", "")).upper() == "CERTIFIED"
    cert_ok = bool((cap.get("certification") or {}).get("certified", False))
    return status_ok or cert_ok

def normalize(s: str) -> str:
    return (s or "").strip().lower()

def match_triggers(cap: dict[str, Any], text: str) -> bool:
    triggers = cap.get("triggers") or []
    t = normalize(text)
    for trig in triggers:
        if normalize(trig) and normalize(trig) in t:
            return True
    return False

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("text", help="Operator text (what you asked Heimdall)")
    ap.add_argument("--max", type=int, default=3, help="Max suggestions (default 3)")
    args = ap.parse_args()

    data = load_registry()
    policy = data.get("policy") or {}
    max_suggestions = int(policy.get("max_suggestions", args.max))
    max_suggestions = min(max_suggestions, 3)  # hard cap

    caps = data.get("capabilities", [])
    if not isinstance(caps, list):
        raise SystemExit("[ERR] registry.json must contain a 'capabilities' array")

    candidates = []
    for cap in caps:
        if not is_certified(cap):
            continue
        if match_triggers(cap, args.text):
            candidates.append(cap)

    out = {
        "at": utc_now_iso(),
        "input": args.text,
        "policy": {
            "auto_surface_requires_certified": True,
            "max_suggestions": max_suggestions,
            "auto_run_never": True,
        },
        "suggestions": [
            {
                "id": c.get("id"),
                "name": c.get("name"),
                "type": c.get("type"),
                "risk_class": c.get("risk_class"),
                "how_to_use": c.get("how_to_use"),
            }
            for c in candidates[:max_suggestions]
        ],
    }

    print(json.dumps(out, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
