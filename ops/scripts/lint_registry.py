from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "ops" / "capabilities" / "registry.json"

def main() -> None:
    if not REGISTRY.exists():
        raise SystemExit(f"[ERR] Missing registry: {REGISTRY}")

    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    caps = data.get("capabilities", [])
    if not isinstance(caps, list):
        raise SystemExit("[ERR] registry.json must contain a 'capabilities' array")

    errors = []
    warnings = []

    for cap in caps:
        cid = cap.get("id", "<missing-id>")
        status = str(cap.get("status", "")).upper()

        cert = cap.get("certification") or {}
        certified = bool(cert.get("certified", False))

        # Missing certification block is a warning (older entries)
        if "certification" not in cap:
            warnings.append(f"{cid}: missing 'certification' block (recommended to add)")

        # Inconsistent status/cert flags
        if status == "CERTIFIED" and not certified:
            errors.append(f"{cid}: status=CERTIFIED but certification.certified=false")

        if certified and status not in ("CERTIFIED", "DORMANT", "LIVE"):
            warnings.append(f"{cid}: certified=true but status='{status}' is unusual")

        # Risk class sanity
        risk = str(cap.get("risk_class", "SAFE")).upper()
        if risk not in ("SAFE", "GATED", "DANGEROUS"):
            warnings.append(f"{cid}: unknown risk_class='{risk}' (expected SAFE|GATED|DANGEROUS)")

        # Command path check (non-executing)
        how = cap.get("how_to_use", {}) or {}
        cmd = (how.get("command") or "").strip()
        if cmd:
            candidate = cmd.split()[-1]
            if candidate.startswith(("ops/", "ops\\")):
                p = (ROOT / candidate).resolve()
                if not p.exists():
                    errors.append(f"{cid}: missing referenced path: {candidate}")

    # Print results
    for w in warnings:
        print("[WARN] " + w)
    for e in errors:
        print("[ERR]  " + e)

    if errors:
        raise SystemExit(f"[BLOCKED] Lint failed: {len(errors)} errors")
    print("[OK] Registry lint passed")

if __name__ == "__main__":
    main()
