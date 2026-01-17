from __future__ import annotations
from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "ops" / "handoff" / "output"

PACKS = {
    "EIA": [
        "ops/runbooks/RUNBOOK.md",
        "ops/runbooks/VERIFY_CHECKLIST.md",
        "governance/MONEY_MOVEMENT_POLICY.md",
    ],
    "ACCOUNTANT": [
        "config/caps_limits.json",
        "governance/MONEY_MOVEMENT_POLICY.md",
    ],
    "LAWYER": [
        "governance/MONEY_MOVEMENT_POLICY.md",
    ],
    "INTERNAL": [
        "ops/runbooks/RUNBOOK.md",
        "ops/runbooks/VERIFY_CHECKLIST.md",
        "config/caps_limits.json",
        "governance/MONEY_MOVEMENT_POLICY.md",
    ]
}

def safe_copy(rel_path: str, dest_dir: Path):
    src = ROOT / rel_path
    if not src.exists():
        return False
    dest_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest_dir / src.name)
    return True

def main():
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    base = OUT / f"handoff_{ts}"
    base.mkdir(parents=True, exist_ok=True)

    for pack, files in PACKS.items():
        pdir = base / pack
        pdir.mkdir(parents=True, exist_ok=True)
        (pdir / "README.txt").write_text(
            f"{pack} HANDOFF PACK\nGenerated: {ts} UTC\n\n"
            "NOTE: No secrets should be included. Mask identifiers only.\n"
        )
        for f in files:
            safe_copy(f, pdir)

    print(f"[OK] Generated handoff packs at: {base}")

if __name__ == "__main__":
    main()
