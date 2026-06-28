from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4


IN_MEMORY_DEALS: Dict[str, Dict[str, Any]] = {}
IN_MEMORY_BUYERS: Dict[str, Dict[str, Any]] = {}
IN_MEMORY_TASKS: Dict[str, Dict[str, Any]] = {}
IN_MEMORY_APPROVALS: Dict[str, Dict[str, Any]] = {}
IN_MEMORY_MESSAGES: Dict[str, Dict[str, Any]] = {}


def now_iso() -> str:
    return datetime.utcnow().isoformat()


def create_deal_record(deal: Dict[str, Any]) -> Dict[str, Any]:
    deal_id = deal.get("id") or f"deal_{uuid4().hex[:12]}"

    record = {
        **deal,
        "id": deal_id,
        "state": deal.get("state", "NEW_LEAD"),
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "state_history": deal.get("state_history", []),
    }

    IN_MEMORY_DEALS[deal_id] = record
    return record


def get_deal_record(deal_id: str) -> Optional[Dict[str, Any]]:
    return IN_MEMORY_DEALS.get(deal_id)


def update_deal_record(deal_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    existing = IN_MEMORY_DEALS.get(deal_id)
    if not existing:
        return None

    existing.update(updates)
    existing["updated_at"] = now_iso()
    IN_MEMORY_DEALS[deal_id] = existing
    return existing


def list_deal_records() -> List[Dict[str, Any]]:
    return list(IN_MEMORY_DEALS.values())


def create_buyer_record(buyer: Dict[str, Any]) -> Dict[str, Any]:
    buyer_id = buyer.get("id") or f"buyer_{uuid4().hex[:12]}"

    record = {
        **buyer,
        "id": buyer_id,
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }

    IN_MEMORY_BUYERS[buyer_id] = record
    return record


def list_buyer_records() -> List[Dict[str, Any]]:
    return list(IN_MEMORY_BUYERS.values())


def create_task_record(task: Dict[str, Any]) -> Dict[str, Any]:
    task_id = task.get("id") or f"task_{uuid4().hex[:12]}"

    record = {
        **task,
        "id": task_id,
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }

    IN_MEMORY_TASKS[task_id] = record
    return record


def list_task_records(deal_id: Optional[str] = None) -> List[Dict[str, Any]]:
    tasks = list(IN_MEMORY_TASKS.values())

    if deal_id:
        tasks = [task for task in tasks if task.get("deal_id") == deal_id]

    return tasks


def create_approval_record(approval: Dict[str, Any]) -> Dict[str, Any]:
    approval_id = approval.get("id") or f"approval_{uuid4().hex[:12]}"

    record = {
        **approval,
        "id": approval_id,
        "status": approval.get("status", "PENDING"),
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }

    IN_MEMORY_APPROVALS[approval_id] = record
    return record


def update_approval_record(approval_id: str, status: str, reviewed_by: str, notes: str = "") -> Optional[Dict[str, Any]]:
    existing = IN_MEMORY_APPROVALS.get(approval_id)
    if not existing:
        return None

    existing.update({
        "status": status,
        "reviewed_by": reviewed_by,
        "reviewed_at": now_iso(),
        "review_notes": notes,
        "updated_at": now_iso(),
    })

    IN_MEMORY_APPROVALS[approval_id] = existing
    return existing


def list_approval_records() -> List[Dict[str, Any]]:
    return list(IN_MEMORY_APPROVALS.values())


def create_message_record(message: Dict[str, Any]) -> Dict[str, Any]:
    message_id = message.get("id") or f"message_{uuid4().hex[:12]}"

    record = {
        **message,
        "id": message_id,
        "status": message.get("status", "DRAFT"),
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }

    IN_MEMORY_MESSAGES[message_id] = record
    return record


def list_message_records(deal_id: Optional[str] = None) -> List[Dict[str, Any]]:
    messages = list(IN_MEMORY_MESSAGES.values())

    if deal_id:
        messages = [message for message in messages if message.get("deal_id") == deal_id]

    return messages
