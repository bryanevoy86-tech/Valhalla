from __future__ import annotations

import argparse
import json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "ops" / "logs" / "capability_audit.jsonl"

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--actor", required=True, help="Who performed the action (e.g., Bryan)")
    ap.add_argument("--action", required=True, help="certify|promote|freeze|unfreeze|edit_registry")
    ap.add_argument("--capability_id", default="", help="Capability id (optional)")
    ap.add_argument("--details", default="", help="Free text details")
    ap.add_argument("--data", default="", help="Optional JSON payload string")
    args = ap.parse_args()

    payload = None
    if args.data.strip():
        try:
            payload = json.loads(args.data)
        except Exception:
            payload = {"raw": args.data}

    entry = {
        "at": utc_now_iso(),
        "actor": args.actor,
        "action": args.action,
        "capability_id": args.capability_id,
        "details": args.details,
        "payload": payload
    }

    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    with AUDIT.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(f"[OK] Appended audit log: {AUDIT}")

if __name__ == "__main__":
    main()
