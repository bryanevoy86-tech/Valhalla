from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.finance.approval_gate import FinanceApprovalGate
from app.finance.finance_audit_log import write_finance_audit
from app.finance.risk_controls import evaluate_financial_risk
from app.compliance.eia_finance_rules import evaluate_eia_finance_restrictions

BASE_DIR = Path(__file__).resolve().parent
QUEUE_DIR = BASE_DIR / "approval_queue"
QUEUE_DIR.mkdir(parents=True, exist_ok=True)

FREEZE_FILE = BASE_DIR / "system_freeze.json"


def _queue_path(intent_id: str) -> Path:
    return QUEUE_DIR / f"{intent_id}.json"


def _freeze_state() -> dict[str, Any]:
    if not FREEZE_FILE.exists():
        return {"frozen": False, "reason": None}
    return json.loads(FREEZE_FILE.read_text(encoding="utf-8"))


def set_finance_freeze(frozen: bool, reason: str | None = None) -> dict[str, Any]:
    state = {"frozen": frozen, "reason": reason}
    FREEZE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    write_finance_audit("finance_freeze_changed", state)
    return state


def queue_financial_intent_for_approval(
    deal_id: str,
    intent_id: str,
    amount: float,
    purpose: str,
    payee: str,
    requested_by: str,
) -> dict[str, Any]:
    freeze = _freeze_state()
    gate = FinanceApprovalGate(
        deal_id=deal_id,
        intent_id=intent_id,
        amount=amount,
        purpose=purpose,
        requested_by=requested_by,
    )

    if freeze.get("frozen"):
        gate.block(f"Finance system frozen: {freeze.get('reason') or 'no reason provided'}")

    risk = evaluate_financial_risk(
        {
            "amount": amount,
            "purpose": purpose,
            "payee": payee,
        }
    )
    if risk["blocked"]:
        gate.block("; ".join(risk["reasons"]))

    eia_restrictions = evaluate_eia_finance_restrictions(
        {
            "amount": amount,
            "purpose": purpose,
            "payee": payee,
        }
    )
    if eia_restrictions["blocked"]:
        gate.block("; ".join(eia_restrictions["reasons"]))

    _queue_path(intent_id).write_text(json.dumps(gate.to_dict(), indent=2), encoding="utf-8")

    result = {
        "queued": True,
        "intent_id": intent_id,
        "deal_id": deal_id,
        "approved": gate.approved,
        "blocked": gate.blocked,
        "block_reason": gate.block_reason,
        "risk": risk,
        "eia_restrictions": eia_restrictions,
    }
    write_finance_audit("finance_intent_queued", result)
    return result


def get_financial_intent_status(intent_id: str) -> dict[str, Any]:
    path = _queue_path(intent_id)
    if not path.exists():
        raise FileNotFoundError(f"Finance approval item not found: {intent_id}")
    return json.loads(path.read_text(encoding="utf-8"))


def approve_financial_intent(intent_id: str, approver: str) -> dict[str, Any]:
    path = _queue_path(intent_id)
    if not path.exists():
        raise FileNotFoundError(f"Finance approval item not found: {intent_id}")

    data = json.loads(path.read_text(encoding="utf-8"))
    gate = FinanceApprovalGate(**data)
    gate.approve(approver)

    path.write_text(json.dumps(gate.to_dict(), indent=2), encoding="utf-8")
    result = {
        "intent_id": intent_id,
        "approved": True,
        "approved_by": approver,
        "approved_at": gate.approved_at,
    }
    write_finance_audit("finance_intent_approved", result)
    return result
