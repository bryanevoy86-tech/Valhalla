from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "ops" / "capabilities" / "registry.json"

def main() -> None:
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    caps = data.get("capabilities", [])
    bad = 0

    for cap in caps:
        how = cap.get("how_to_use", {}) or {}
        cmd = (how.get("command") or "").strip()
        if not cmd:
            continue

        candidate = cmd.split()[-1]
        if candidate.startswith(("ops/", "ops\\")):
            p = (ROOT / candidate).resolve()
            if not p.exists():
                bad += 1
                print(f"[BAD] {cap.get('id')} -> missing: {candidate}")

    if bad:
        raise SystemExit(f"[ERR] Registry validation failed: {bad} missing paths")
    print("[OK] Registry validation passed")

if __name__ == "__main__":
    main()
