from datetime import datetime
import json
import os

EIA_DIR = "EIA"
os.makedirs(EIA_DIR, exist_ok=True)

def generate_monthly_report(month=None):
    month = month or datetime.now().strftime("%Y-%m")
    report = {
        "month": month,
        "generated_at": datetime.utcnow().isoformat(),
        "status": "EIA_REPORT_READY",
        "income_summary": [],
        "expense_summary": [],
        "receipt_index": [],
        "bank_checklist": [],
        "notes": [],
    }
    report_path = f"{EIA_DIR}/{month}/EIA_REPORT_{month}.json"
    os.makedirs(f"{EIA_DIR}/{month}", exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    
    return {"path": report_path, "report": report}
