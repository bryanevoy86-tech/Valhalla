#!/usr/bin/env python3
"""
PHASE 2 Engine Promotion — DORMANT → SANDBOX

WHAT THIS DOES:
- Promotes ONE engine from DORMANT to SANDBOX state
- No automatic execution happens
- Logic runs, data flows, logs populate
- No money moves, no real outreach, no irreversible actions

WHAT YOU DO:
- Run this locally (VS Code terminal)
- Promotes wholesaling, then trading_advisory
- Validates state change
- Ready for SANDBOX validation

USAGE:
  python valhalla/promote_engine.py --engine wholesaling --state sandbox
  python valhalla/promote_engine.py --engine trading_advisory --state sandbox
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

import requests


def get_engine_states(api_base: str) -> dict[str, Any]:
    """Get all engine states"""
    resp = requests.get(f"{api_base}/api/engines/states", timeout=15)
    if resp.status_code != 200:
        raise RuntimeError(f"Failed to get engine states: {resp.status_code} - {resp.text}")
    return resp.json()


def transition_engine(api_base: str, engine_name: str, target_state: str) -> dict[str, Any]:
    """Transition an engine to a new state"""
    payload = {
        "engine_name": engine_name,
        "target_state": target_state,
        "changed_by": "heimdall-phase-2",
        "reason": f"PHASE 2: Promote {engine_name} from DORMANT to {target_state.upper()}",
    }
    resp = requests.post(
        f"{api_base}/api/engines/transition",
        json=payload,
        timeout=15,
    )
    if resp.status_code not in [200, 201]:
        raise RuntimeError(f"Failed to transition engine: {resp.status_code} - {resp.text}")
    return resp.json()


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Promote engine to new state")
    parser.add_argument(
        "--api",
        default="https://valhalla-api-ha6a.onrender.com",
        help="API base URL",
    )
    parser.add_argument(
        "--engine",
        required=True,
        help="Engine name: wholesaling, trading_advisory, etc.",
    )
    parser.add_argument(
        "--state",
        required=True,
        help="Target state: sandbox, live (usually sandbox for PHASE 2)",
    )
    args = parser.parse_args(argv)

    print("\n" + "=" * 78)
    print(f"VALHALLA PHASE 2 — Promote {args.engine.upper()}")
    print("=" * 78)
    print()

    try:
        # Step 1: Get current states
        print("[STEP 1] Getting current engine states...")
        states_resp = get_engine_states(args.api)
        engines = {e["engine_name"]: e for e in states_resp.get("engines", [])}

        engine_info = engines.get(args.engine)
        if not engine_info:
            print(f"\n[ERROR] Engine '{args.engine}' not found")
            return 1

        print(f"Current state: {engine_info['state']}")
        print(f"Allowed next states: {engine_info['allowed_next']}")
        print()

        # Step 2: Validate transition is allowed
        if args.state.lower() not in [s.lower() for s in engine_info["allowed_next"]]:
            print(f"[ERROR] Transition to {args.state} not allowed from {engine_info['state']}")
            print(f"Allowed transitions: {engine_info['allowed_next']}")
            return 1

        print(f"[STEP 2] Transitioning {args.engine} to {args.state.upper()}...")
        result = transition_engine(args.api, args.engine, args.state)

        print(f"✓ Engine promoted")
        print(f"New state:")
        print(f"  state: {result['state']}")
        print(f"  allowed_next: {result['allowed_next']}")
        print(f"  changed_by: {result['changed_by']}")
        print(f"  updated_at: {result['updated_at']}")
        print()

        print("=" * 78)
        print("ENGINE PROMOTION COMPLETE")
        print("=" * 78)
        print()

        if result["state"].upper() == "SANDBOX":
            print(f"✓ {args.engine} is now in SANDBOX")
            print()
            print("Next steps:")
            print(f"  1) Validate {args.engine} behavior in SANDBOX (no real-world impact)")
            print("  2) Run PHASE 2 validation tests")
            print("  3) When ready, promote next engine")
            print()

        return 0

    except Exception as e:
        print(f"\n[ERROR] {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
