from __future__ import annotations
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "ops" / "handoff" / "output"

STRUCTURE = [
    "01_Summary",
    "02_Income_and_Expenses",
    "03_Ledger_Exports",
    "04_Tax_Notes",
    "05_Banking_Map_Masked",
    "06_Receipts_If_Any"
]

def main():
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    base = OUT / f"ACCOUNTANT_SNAPSHOT_{ts}"
    base.mkdir(parents=True, exist_ok=True)

    for d in STRUCTURE:
        (base / d).mkdir(parents=True, exist_ok=True)

    (base / "01_Summary" / "SUMMARY.md").write_text(
        "# Accountant Snapshot (Draft)\n\n"
        f"Generated: {ts} UTC\n\n"
        "- Period:\n- Revenue summary:\n- Expense summary:\n- Notes:\n"
    )

    (base / "05_Banking_Map_Masked" / "BANKING_MAP_MASKED.md").write_text(
        "# Banking Map (Masked)\n\n"
        "Rules:\n"
        "- No full account numbers\n"
        "- Last 4 digits only\n\n"
        "Accounts:\n"
        "- OPERATING:\n- TAX:\n- RESERVE:\n- TRUST:\n- DEAL_STAGING:\n- CREDIT:\n"
    )

    print(f"[OK] Accountant snapshot generated: {base}")

if __name__ == "__main__":
    main()
