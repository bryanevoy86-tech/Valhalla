from __future__ import annotations

import argparse
import json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "ops" / "capabilities" / "registry.json"
FREEZE = ROOT / "ops" / "capabilities" / "freeze.json"
AUDIT = ROOT / "ops" / "logs" / "capability_audit.jsonl"

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def append_audit(actor: str, action: str, capability_id: str, details: str) -> None:
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "at": utc_now_iso(),
        "actor": actor,
        "action": action,
        "capability_id": capability_id,
        "details": details,
        "payload": None
    }
    with AUDIT.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def frozen() -> bool:
    if not FREEZE.exists():
        return False
    try:
        return bool(json.loads(FREEZE.read_text(encoding="utf-8")).get("frozen", False))
    except Exception:
        return False

def load_registry() -> dict:
    if not REGISTRY.exists():
        raise SystemExit(f"[ERR] Missing registry: {REGISTRY}")
    return json.loads(REGISTRY.read_text(encoding="utf-8"))

def save_registry(d: dict) -> None:
    REGISTRY.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def ensure_cert_block(cap: dict) -> None:
    cap.setdefault("certification", {})
    cap["certification"].setdefault("certified", False)
    cap["certification"].setdefault("certified_at", None)
    cap["certification"].setdefault("certified_by", None)
    cap["certification"].setdefault("cert_notes", "")
    cap["certification"].setdefault("test_log", [])

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--by", required=True, help="Actor (e.g., Bryan)")
    ap.add_argument("--notes", default="", help="Default notes for all certifications")
    ap.add_argument("--ids", nargs="+", required=True, help="Capability ids to certify")
    ap.add_argument("--test", action="append", default=[], help="Test log line (repeatable)")
    args = ap.parse_args()

    if frozen():
        raise SystemExit("[ERR] Capabilities are frozen. Unfreeze to certify.")

    data = load_registry()
    caps = data.get("capabilities", [])
    if not isinstance(caps, list):
        raise SystemExit("[ERR] registry.json must contain a 'capabilities' array")

    id_set = set(args.ids)
    found = 0

    for cap in caps:
        if cap.get("id") in id_set:
            found += 1
            ensure_cert_block(cap)
            cap["certification"]["certified"] = True
            cap["certification"]["certified_at"] = utc_now_iso()
            cap["certification"]["certified_by"] = args.by
            cap["certification"]["cert_notes"] = args.notes

            for t in args.test:
                cap["certification"]["test_log"].append({"at": utc_now_iso(), "line": t})

            # Align top-level status
            cap["status"] = "CERTIFIED"

            append_audit(args.by, "certify", cap.get("id", ""), args.notes or "batch_certify")

    missing = id_set - {c.get("id") for c in caps}
    save_registry(data)

    print(f"[OK] Certified {found} capabilities.")
    if missing:
        print("[WARN] These ids were not found in registry:")
        for m in sorted(missing):
            print(" - " + m)

if __name__ == "__main__":
    main()
