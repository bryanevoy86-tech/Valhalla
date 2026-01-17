from __future__ import annotations
import argparse
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "ops" / "handoff" / "output"

DEAL_PACKET_STRUCTURE = [
    "01_Summary",
    "02_Lead_Details",
    "03_Financials",
    "04_Photos_If_Any",
    "05_Comps_If_Any",
    "06_Contracts_Drafts",
    "07_Legal_Notes",
    "08_Communications_Logs"
]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--deal-id", required=True, help="Deal identifier (e.g., D001)")
    ap.add_argument("--label", default="", help="Optional label for folder naming")
    args = ap.parse_args()

    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_label = args.label.strip().replace(" ", "_")
    folder_name = f"DEAL_{args.deal_id}_{safe_label}_{ts}".strip("_")

    base = OUT / folder_name
    base.mkdir(parents=True, exist_ok=True)

    for d in DEAL_PACKET_STRUCTURE:
        (base / d).mkdir(parents=True, exist_ok=True)

    # Minimal starter docs (no secrets)
    (base / "01_Summary" / "SUMMARY.md").write_text(
        f"# Deal Summary\n\nDeal ID: {args.deal_id}\nGenerated: {ts} UTC\n\n"
        "- What is the property?\n- What is the ask?\n- What is the strategy?\n- What are the risks?\n"
    )
    (base / "07_Legal_Notes" / "LEGAL_NOTES.md").write_text(
        "# Legal Notes (Draft)\n\n- Title status:\n- Known encumbrances:\n- Required clauses:\n- Questions for lawyer:\n"
    )

    print(f"[OK] Deal packet generated: {base}")

if __name__ == "__main__":
    main()
