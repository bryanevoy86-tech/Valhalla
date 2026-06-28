from typing import Any, Dict

from sqlalchemy.orm import Session

from app.heimdall.education.deal_intake_orchestrator import run_full_deal_intake
from app.heimdall.services.persistence_service import (
    create_deal,
    update_deal,
    create_task,
    create_approval,
    create_message,
)


def run_and_persist_deal_intake(db: Session, payload: Dict[str, Any]) -> Dict[str, Any]:
    intake_result = run_full_deal_intake(payload)

    deal_data = intake_result.get("pipeline", {}).get("updated_deal") or intake_result.get("deal", {})
    saved_deal = create_deal(db, deal_data)

    deal_id = saved_deal.id

    # Save updated pipeline state if present
    pipeline_updated_deal = intake_result.get("pipeline", {}).get("updated_deal")
    if pipeline_updated_deal:
        update_deal(db, deal_id, pipeline_updated_deal)

    # Save VA tasks
    saved_tasks = []
    for task in intake_result.get("va_tasks", {}).get("tasks", []):
        task_record = create_task(db, {
            **task,
            "deal_id": deal_id,
            "property_address": deal_data.get("property_address"),
        })
        saved_tasks.append(task_record.id)

    # Save approval records
    saved_approvals = []
    for approval in intake_result.get("approval_items", []):
        approval_record = create_approval(db, {
            **approval,
            "deal_id": deal_id,
        })
        saved_approvals.append(approval_record.id)

    # Save seller message draft
    seller_message = intake_result.get("seller_message")
    saved_messages = []

    if seller_message:
        message_record = create_message(db, {
            "deal_id": deal_id,
            "recipient_type": "seller",
            "status": "DRAFT_PENDING_APPROVAL",
            "message_type": seller_message.get("message_type"),
            "payload": seller_message,
            "body": seller_message.get("draft_message"),
        })
        saved_messages.append(message_record.id)

    # Save buyer outreach drafts
    buyer_queue = intake_result.get("buyer_outreach_queue")
    if buyer_queue:
        for item in buyer_queue.get("approval_queue", []):
            message_record = create_message(db, {
                "deal_id": deal_id,
                "recipient_type": "buyer",
                "recipient_id": item.get("buyer_id"),
                "recipient_name": item.get("buyer_name"),
                "status": "DRAFT_PENDING_APPROVAL",
                "message_type": "buyer_interest_check",
                "payload": item,
                "body": item.get("message"),
            })
            saved_messages.append(message_record.id)

    return {
        "status": "INTAKE_PERSISTED",
        "deal_id": deal_id,
        "saved_task_ids": saved_tasks,
        "saved_approval_ids": saved_approvals,
        "saved_message_ids": saved_messages,
        "heimdall_command": intake_result.get("heimdall_command"),
        "pipeline": intake_result.get("pipeline"),
        "human_approval_required": True,
        "send_blocked_until_approved": True,
        "contract_blocked_until_lawyer_review": True,
    }
