from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FREEZE = ROOT / "ops" / "capabilities" / "freeze.json"
OUTDIR = ROOT / "ops" / "handoff" / "output"

def run(cmd: list[str]) -> tuple[int, str]:
    p = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
    out = (p.stdout or "") + (p.stderr or "")
    return p.returncode, out.strip()

def main() -> None:
    results = {"READY": True, "WARNINGS": [], "BLOCKERS": []}

    # Output dir check
    if not OUTDIR.exists():
        results["WARNINGS"].append(f"Missing output dir: {OUTDIR} (creating is recommended)")
    else:
        pass

    # Freeze file exists
    if not FREEZE.exists():
        results["WARNINGS"].append(f"Missing freeze file: {FREEZE} (run freeze script once to create)")
        frozen = None
    else:
        frozen_data = json.loads(FREEZE.read_text(encoding="utf-8"))
        frozen = bool(frozen_data.get("frozen", False))
        if frozen:
            results["WARNINGS"].append("Capabilities are FROZEN (expected at GO-time).")

    # Registry lint
    rc, out = run(["python", "ops/scripts/lint_registry.py"])
    if rc != 0:
        results["READY"] = False
        results["BLOCKERS"].append("Registry lint failed")
        results["BLOCKERS"].append(out)
    else:
        results["WARNINGS"].append("Registry lint passed")

    # Certified-only suggestion check (won't fail build if none are certified yet)
    rc2, out2 = run(["python", "ops/scripts/suggest_certified.py", "accountant taxes monthly books"])
    if rc2 != 0:
        results["WARNINGS"].append("suggest_certified.py did not run cleanly")
        results["WARNINGS"].append(out2)
    else:
        results["WARNINGS"].append("suggest_certified.py ran")

    # Print summary
    print("=== COLD-ZONE CHECK ===")
    if results["READY"]:
        print("✅ READY")
    else:
        print("❌ BLOCKED")

    if results["BLOCKERS"]:
        print("\n--- BLOCKERS ---")
        for b in results["BLOCKERS"]:
            print(b)

    if results["WARNINGS"]:
        print("\n--- NOTES ---")
        for w in results["WARNINGS"]:
            print(w)

if __name__ == "__main__":
    main()
