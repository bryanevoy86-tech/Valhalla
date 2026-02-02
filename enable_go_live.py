#!/usr/bin/env python3
"""
Local Go-Live Enable Script

Run this AFTER the governance_go_live router is deployed to Render.
This script enables go_live.enabled = true with kill_switch_engaged = false.

USAGE:
  python valhalla/enable_go_live.py --api https://valhalla-api-ha6a.onrender.com

WHAT IT DOES:
  1. Fetches current go_live state
  2. Verifies checklist is clear
  3. Enables go_live (sets go_live_enabled=true, kill_switch_engaged=false)
  4. Engines remain DORMANT (no automatic execution)
  5. Prints the new state

PHASE DESCRIPTION:
  PHASE 1 — Remove the master lock
  - This is a permission flip, not execution
  - Engines remain DORMANT
  - This is safe
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

import requests


def get_state(api_base: str) -> dict[str, Any]:
    """Fetch current go_live state"""
    resp = requests.get(f"{api_base}/api/governance/go-live/state", timeout=15)
    if resp.status_code != 200:
        raise RuntimeError(f"Failed to get state: {resp.status_code} - {resp.text}")
    return resp.json()


def get_checklist(api_base: str) -> dict[str, Any]:
    """Fetch go_live checklist"""
    resp = requests.get(f"{api_base}/api/governance/go-live/checklist", timeout=15)
    if resp.status_code != 200:
        raise RuntimeError(f"Failed to get checklist: {resp.status_code} - {resp.text}")
    return resp.json()


def enable_go_live(api_base: str) -> dict[str, Any]:
    """Enable go_live"""
    payload = {
        "enabled": True,
        "changed_by": "heimdall-phase-1",
        "reason": "PHASE 1: Initial go_live enable - engines remain DORMANT",
    }
    resp = requests.post(
        f"{api_base}/api/governance/go-live/enable",
        json=payload,
        timeout=15,
    )
    if resp.status_code not in [200, 201]:
        raise RuntimeError(f"Failed to enable go_live: {resp.status_code} - {resp.text}")
    return resp.json()


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Enable go_live for Valhalla")
    parser.add_argument(
        "--api",
        default="https://valhalla-api-ha6a.onrender.com",
        help="API base URL",
    )
    args = parser.parse_args(argv)

    print("\n" + "=" * 78)
    print("VALHALLA PHASE 1 — Enable Go-Live")
    print("=" * 78)
    print()

    try:
        # Step 1: Check current state
        print("[STEP 1] Checking current state...")
        state = get_state(args.api)
        print(f"Current state:")
        print(f"  go_live_enabled: {state.get('go_live_enabled')}")
        print(f"  kill_switch_engaged: {state.get('kill_switch_engaged')}")
        print()

        # Step 2: Check checklist
        print("[STEP 2] Verifying checklist...")
        checklist = get_checklist(args.api)
        print(f"Checklist status: {json.dumps(checklist, indent=2)}")
        if not checklist.get("ok"):
            print("\n[WARNING] Checklist has blockers:")
            for blocker in checklist.get("blockers", []):
                print(f"  - {blocker}")
            resp = input("\nProceed anyway? (y/N): ").strip().lower()
            if resp != "y":
                print("Aborted.")
                return 1
        print()

        # Step 3: Enable go_live
        print("[STEP 3] Enabling go_live.enabled = true...")
        new_state = enable_go_live(args.api)
        print(f"✓ Go-live ENABLED")
        print(f"New state:")
        print(f"  go_live_enabled: {new_state.get('go_live_enabled')}")
        print(f"  kill_switch_engaged: {new_state.get('kill_switch_engaged')}")
        print(f"  updated_at: {new_state.get('updated_at')}")
        print(f"  changed_by: {new_state.get('changed_by')}")
        print()

        print("=" * 78)
        print("PHASE 1 COMPLETE")
        print("=" * 78)
        print()
        print("✓ Go-live is enabled. Engines are still DORMANT.")
        print()
        print("Next: Move engines to SANDBOX")
        print("  python valhalla/promote_engine.py --engine wholesaling --state sandbox")
        print()

        return 0

    except Exception as e:
        print(f"\n[ERROR] {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
