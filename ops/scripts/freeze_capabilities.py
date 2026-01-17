from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FREEZE = ROOT / "ops" / "capabilities" / "freeze.json"

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def load() -> dict:
    if not FREEZE.exists():
        FREEZE.parent.mkdir(parents=True, exist_ok=True)
        FREEZE.write_text(json.dumps({"frozen": False, "frozen_at": None, "frozen_by": None, "reason": ""}, indent=2) + "\n", encoding="utf-8")
    return json.loads(FREEZE.read_text(encoding="utf-8"))

def save(d: dict) -> None:
    FREEZE.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["on", "off", "status"])
    ap.add_argument("--by", default="")
    ap.add_argument("--reason", default="")
    args = ap.parse_args()

    d = load()

    if args.mode == "status":
        print(json.dumps(d, indent=2, ensure_ascii=False))
        return

    if args.mode == "on":
        d["frozen"] = True
        d["frozen_at"] = utc_now_iso()
        d["frozen_by"] = args.by or d.get("frozen_by")
        d["reason"] = args.reason or d.get("reason", "")
        save(d)
        print("[OK] Capabilities frozen")
        return

    if args.mode == "off":
        d["frozen"] = False
        d["frozen_at"] = utc_now_iso()
        d["frozen_by"] = args.by or d.get("frozen_by")
        d["reason"] = args.reason or d.get("reason", "")
        save(d)
        print("[OK] Capabilities unfrozen")
        return

if __name__ == "__main__":
    main()
