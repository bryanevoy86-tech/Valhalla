from typing import Any, Dict, List

from app.heimdall.education.unified_deal_command_engine import unified_deal_command
from app.heimdall.education.document_packet_engine import prepare_deal_packets
from app.heimdall.education.seller_message_engine import draft_seller_message
from app.heimdall.education.va_task_routing_engine import route_va_tasks
from app.heimdall.education.deal_pipeline_state_machine import advance_deal_state
from app.heimdall.education.buyer_outreach_queue import build_buyer_outreach_queue


def build_initial_deal_record(payload: Dict[str, Any]) -> Dict[str, Any]:
    deal = payload.get("deal", {})

    return {
        **deal,
        "state": deal.get("state", "NEW_LEAD"),
        "source": deal.get("source", "heimdall_intake"),
        "state_history": deal.get("state_history", []),
    }


def create_approval_items(
    deal: Dict[str, Any],
    command_result: Dict[str, Any],
    packets: Dict[str, Any],
    seller_message: Dict[str, Any],
    buyer_queue: Dict[str, Any] | None,
) -> List[Dict[str, Any]]:
    approvals = []

    approvals.append({
        "deal_id": deal.get("id"),
        "approval_type": "heimdall_command",
        "status": "PENDING",
        "title": "Approve Heimdall deal command",
        "payload": command_result,
    })

    approvals.append({
        "deal_id": deal.get("id"),
        "approval_type": "seller_message",
        "status": "PENDING",
        "title": "Approve seller message draft",
        "payload": seller_message,
    })

    approvals.append({
        "deal_id": deal.get("id"),
        "approval_type": "lawyer_packet",
        "status": "PENDING",
        "title": "Approve lawyer review packet before sending",
        "payload": packets.get("packets", {}).get("lawyer_review_packet"),
    })

    if buyer_queue:
        for item in buyer_queue.get("approval_queue", []):
            approvals.append({
                "deal_id": deal.get("id"),
                "approval_type": "buyer_outreach",
                "status": "PENDING",
                "title": f"Approve buyer outreach to {item.get('buyer_name')}",
                "payload": item,
            })

    return approvals


def run_full_deal_intake(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Full orchestration flow:
    1. Build initial deal record
    2. Run unified command engine
    3. Prepare document packets
    4. Draft seller message
    5. Build buyer outreach queue if buyer matches exist
    6. Route VA tasks
    7. Advance pipeline state
    8. Return approval items
    """

    deal = build_initial_deal_record(payload)

    command_output = unified_deal_command(payload)
    command_result = command_output.get("heimdall_command", {})

    enriched_deal = {
        **deal,
        "mao": command_output.get("subsystem_results", {})
            .get("underwriting", {})
            .get("mao"),
        "projected_spread": command_output.get("subsystem_results", {})
            .get("underwriting", {})
            .get("projected_spread"),
        "red_flags": command_result.get("red_flags", []),
        "missing_documents": command_result.get("missing_data", []),
    }

    packets = prepare_deal_packets(enriched_deal)

    seller_message = draft_seller_message(
        deal=enriched_deal,
        command_result=command_result,
    )

    buyer_queue = None
    buyer_match_result = command_output.get("subsystem_results", {}).get("buyer_matching")

    if buyer_match_result and buyer_match_result.get("recommended_send_list"):
        buyer_queue = build_buyer_outreach_queue(
            deal=enriched_deal,
            matched_buyers=buyer_match_result.get("recommended_send_list", []),
        )

    va_tasks = route_va_tasks(
        command_result=command_result,
        deal=enriched_deal,
    )

    pipeline_result = advance_deal_state(
        deal=enriched_deal,
        command_result=command_result,
        advanced_by="heimdall_intake_orchestrator",
    )

    approvals = create_approval_items(
        deal=enriched_deal,
        command_result=command_result,
        packets=packets,
        seller_message=seller_message,
        buyer_queue=buyer_queue,
    )

    return {
        "status": "INTAKE_COMPLETE",
        "deal": enriched_deal,
        "heimdall_command": command_result,
        "pipeline": pipeline_result,
        "packets": packets,
        "seller_message": seller_message,
        "buyer_outreach_queue": buyer_queue,
        "va_tasks": va_tasks,
        "approval_items": approvals,
        "human_approval_required": True,
        "send_blocked_until_approved": True,
        "contract_blocked_until_lawyer_review": True,
    }
