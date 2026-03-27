from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Dict, List

CORP_STARTER = [
    "Register entity (articles/incorp/LLC filing)",
    "Get business number / tax account",
    "Open business bank account",
    "Set signing authority + minute book",
    "Set bookkeeping categories + receipt flow",
]
TRUST_STARTER = [
    "Draft trust deed (lawyer)",
    "Appoint trustees + beneficiaries",
    "Open trust bank account (if applicable)",
    "Set asset transfer plan",
    "Document storage + proof packs",
]
BANK_STARTER = [
    "Choose bank + account type",
    "Prepare KYC docs (ID, address, incorporation docs)",
    "Set e-transfers / wires / limits",
    "Enable alerts + statements delivery",
]

def apply_template(entity_id: str, template: str, due_days: int = 30, create_followups: bool = True) -> Dict[str, Any]:
    warnings: List[str] = []
    template_key = (template or "").strip().lower()
    if template_key not in ("corp","trust","bank"):
        raise ValueError("template must be corp|trust|bank")

    items = CORP_STARTER if template_key == "corp" else TRUST_STARTER if template_key == "trust" else BANK_STARTER
    created_tasks = []
    try:
        from backend.app.core_gov.entity_tracker import service as ets  # type: ignore
        for i, title in enumerate(items):
            due = (date.today() + timedelta(days=min(int(due_days or 30), 365))).isoformat()
            t = ets.add_task(entity_id=entity_id, title=title, status="open", due_date=due, priority="normal", requires_doc=(template_key in ("trust","bank")))
            created_tasks.append(t)
    except Exception as e:
        raise RuntimeError(f"entity_tracker unavailable: {type(e).__name__}: {e}")

    created_followups = 0
    if create_followups:
        try:
            from backend.app.followups import store as fstore  # type: ignore
            for t in created_tasks:
                try:
                    fstore.create_followup({
                        "type": "entity_task",
                        "entity_id": entity_id,
                        "task_id": t.get("id",""),
                        "title": f"Entity task: {t.get('title','')}",
                        "due_date": t.get("due_date",""),
                        "status": "open",
                    })
                    created_followups += 1
                except Exception:
                    warnings.append("followups: create_followup not found or failed (safe)")
                    break
        except Exception as e:
            warnings.append(f"followups unavailable: {type(e).__name__}: {e}")

    return {"entity_id": entity_id, "template": template_key, "tasks_created": len(created_tasks), "followups_created": created_followups, "warnings": warnings}
