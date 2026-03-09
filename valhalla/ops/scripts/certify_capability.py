from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "ops" / "capabilities" / "registry.json"
FREEZE = ROOT / "ops" / "capabilities" / "freeze.json"

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def load_registry() -> dict:
    if not REGISTRY.exists():
        raise SystemExit(f"[ERR] Registry not found: {REGISTRY}")
    return json.loads(REGISTRY.read_text(encoding="utf-8"))

def save_registry(data: dict) -> None:
    REGISTRY.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def ensure_cert_block(cap: dict) -> None:
    cap.setdefault("certification", {})
    cap["certification"].setdefault("certified", False)
    cap["certification"].setdefault("certified_at", None)
    cap["certification"].setdefault("certified_by", None)
    cap["certification"].setdefault("cert_notes", "")
    cap["certification"].setdefault("test_log", [])

def verify_paths(cap: dict) -> list[str]:
    """
    Verifies that any referenced 'command' target exists when it looks like a file path.
    This is deliberately conservative; it does NOT execute anything.
    """
    issues: list[str] = []
    how = cap.get("how_to_use", {}) or {}
    cmd = (how.get("command") or "").strip()
    if not cmd:
        return issues

    parts = cmd.split()
    # Heuristic: last token is the path for "open ...", "cat ...", "python .../file.py"
    candidate = parts[-1]

    # Only check local repo paths
    if candidate.startswith(("ops/", "ops\\")):
        path = (ROOT / candidate).resolve()
        if not path.exists():
            issues.append(f"Referenced path does not exist: {candidate}")
    return issues

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("capability_id", help="Capability id in registry.json (e.g., deal_packet_generator)")
    ap.add_argument("--by", required=True, help="Who is certifying (e.g., Bryan)")
    ap.add_argument("--notes", default="", help="Certification notes")
    ap.add_argument("--test", action="append", default=[], help="Add a test log line (repeatable)")
    ap.add_argument("--force", action="store_true", help="Allow certify even if path checks fail (not recommended)")
    args = ap.parse_args()

    # Check if capabilities are frozen
    if FREEZE.exists():
        frozen = json.loads(FREEZE.read_text(encoding="utf-8")).get("frozen", False)
        if frozen:
            raise SystemExit("[ERR] Capabilities are frozen. Unfreeze to certify.")

    data = load_registry()
    caps = data.get("capabilities", [])
    if not isinstance(caps, list):
        raise SystemExit("[ERR] registry.json must contain a 'capabilities' array")

    target = None
    for c in caps:
        if c.get("id") == args.capability_id:
            target = c
            break

    if not target:
        raise SystemExit(f"[ERR] Capability id not found: {args.capability_id}")

    ensure_cert_block(target)

    issues = verify_paths(target)
    if issues and not args.force:
        print("[ERR] Path verification failed. Fix these before certifying:")
        for i in issues:
            print(" - " + i)
        print("\nIf you *must* override, re-run with --force (not recommended).")
        raise SystemExit(2)

    # Mark certified
    target["certification"]["certified"] = True
    target["certification"]["certified_at"] = utc_now_iso()
    target["certification"]["certified_by"] = args.by
    target["certification"]["cert_notes"] = args.notes
    for t in args.test:
        target["certification"]["test_log"].append({"at": utc_now_iso(), "line": t})

    # Optional: align top-level status too
    # Keep DORMANT as status (safe), but certified true allows auto-surface.
    # If you prefer: set status="CERTIFIED"
    if target.get("status") == "DORMANT":
        target["status"] = "CERTIFIED"

    save_registry(data)
    print(f"[OK] Certified capability: {args.capability_id}")

if __name__ == "__main__":
    main()
