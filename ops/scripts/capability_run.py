from __future__ import annotations
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "ops" / "capabilities" / "registry.json"


def load_registry():
    return json.loads(REGISTRY_PATH.read_text())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("capability_id")
    args = ap.parse_args()

    reg = load_registry()
    caps = {c["id"]: c for c in reg.get("capabilities", [])}

    if args.capability_id not in caps:
        raise SystemExit(f"Unknown capability id: {args.capability_id}")

    cap = caps[args.capability_id]
    how = cap.get("how_to_use", {})
    print("\n=== CAPABILITY RUNNER (SAFE) ===")
    print(f"ID: {cap.get('id')}")
    print(f"NAME: {cap.get('name')}")
    print(f"STATUS: {cap.get('status')}")
    print(f"RISK: {cap.get('risk_class')}")
    print("\nHOW TO USE:")
    print(f" - mode: {how.get('mode')}")
    print(f" - command: {how.get('command')}")
    print(f" - notes: {how.get('notes')}")
    print("\nNOTE: This runner does NOT auto-execute anything. It only prints the approved command.\n")


if __name__ == "__main__":
    main()
