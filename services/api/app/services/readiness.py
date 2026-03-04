"""
PACK CL20: System Readiness
Computes "green light" readiness score for launch.
"""

from sqlalchemy.orm import Session

from app.models.execution_checklist import ExecutionChecklistItem
from app.models.activation_gate import ActivationGate


def compute_readiness(db: Session) -> dict:
    checklist = db.query(ExecutionChecklistItem).all()
    gates = db.query(ActivationGate).all()

    total_items = len(checklist)
    completed = sum(1 for i in checklist if i.is_complete)

    checklist_score = 100 if total_items == 0 else int((completed / total_items) * 100)

    blocked_gates = [g.gate_key for g in gates if not g.is_enabled]
    locked_gates = [g.gate_key for g in gates if g.is_locked]

    ready = checklist_score >= 80 and len(blocked_gates) == 0 and len(locked_gates) == 0

    missing = []
    if checklist_score < 80:
        missing.append("Execution checklist below 80%")
    if blocked_gates:
        missing.append(f"Blocked gates: {blocked_gates}")
    if locked_gates:
        missing.append(f"Locked gates: {locked_gates}")

    return {
        "ready": ready,
        "checklist_score": checklist_score,
        "checklist_total": total_items,
        "checklist_completed": completed,
        "blocked_gates": blocked_gates,
        "locked_gates": locked_gates,
        "missing": missing,
    }
