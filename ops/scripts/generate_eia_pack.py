from __future__ import annotations
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "ops" / "handoff" / "output"

STRUCTURE = [
    "01_Executive_Summary",
    "02_System_Overview",
    "03_Timeline_44_Weeks",
    "04_Budget_and_Runway",
    "05_Risk_and_Safeguards",
    "06_Proof_Sandbox_Status",
    "07_Appendix"
]

def main():
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    base = OUT / f"EIA_PACK_{ts}"
    base.mkdir(parents=True, exist_ok=True)

    for d in STRUCTURE:
        (base / d).mkdir(parents=True, exist_ok=True)

    (base / "01_Executive_Summary" / "EXEC_SUMMARY.md").write_text(
        "# Executive Summary (Draft)\n\n"
        "- What the business is\n- What problem it solves\n- How it earns revenue\n- Why it is viable\n"
    )
    (base / "03_Timeline_44_Weeks" / "TIMELINE.md").write_text(
        "# 44-Week Timeline (Draft)\n\n"
        "- Week 0–4: Setup + first cycles\n- Week 5–12: Consistent deal flow\n- Week 13–24: Stabilization + refinement\n- Week 25–44: Scale + compliance\n"
    )
    (base / "05_Risk_and_Safeguards" / "SAFETY.md").write_text(
        "# Risk & Safeguards\n\n"
        "- DRY-RUN protections in sandbox\n- Approval gates for irreversible actions\n- Caps, whitelists, kill switch\n"
    )

    print(f"[OK] EIA pack generated: {base}")

if __name__ == "__main__":
    main()
