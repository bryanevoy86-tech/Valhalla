from typing import Any, Dict, List


def build_missing_documents_checklist(deal: Dict[str, Any]) -> List[str]:
    checklist = []

    if not deal.get("seller_authority_verified"):
        checklist.append("Proof of seller ownership/authority")

    if not deal.get("arv_supported"):
        checklist.append("Comparable sales supporting ARV")

    if not deal.get("repair_estimate_attached"):
        checklist.append("Repair estimate or conservative repair worksheet")

    if not deal.get("buyer_demand_verified"):
        checklist.append("Buyer demand proof / soft buyer interest")

    if not deal.get("tax_status_checked"):
        checklist.append("Property tax status / arrears check")

    if not deal.get("title_status_checked"):
        checklist.append("Title/lien status check")

    if not deal.get("photos_attached"):
        checklist.append("Property photos")

    if not deal.get("seller_disclosure_attached"):
        checklist.append("Seller disclosure / known issues summary")

    return checklist


def build_seller_offer_summary(deal: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "packet_type": "seller_offer_summary",
        "property_address": deal.get("property_address"),
        "seller_name": deal.get("seller_name"),
        "recommended_offer": deal.get("recommended_offer"),
        "maximum_allowable_offer": deal.get("mao"),
        "reasoning": deal.get("offer_reasoning", []),
        "conditions_required": [
            "Seller authority verified",
            "Lawyer review before signing",
            "Title/tax status acceptable",
            "Inspection or repair validation complete",
        ],
        "approval_required": True,
    }


def build_lawyer_review_packet(deal: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "packet_type": "lawyer_review_packet",
        "property_address": deal.get("property_address"),
        "seller_name": deal.get("seller_name"),
        "buyer_or_assignment_plan": deal.get("exit_strategy"),
        "proposed_offer": deal.get("recommended_offer"),
        "mao": deal.get("mao"),
        "known_risks": deal.get("red_flags", []),
        "missing_documents": build_missing_documents_checklist(deal),
        "questions_for_lawyer": [
            "Can this agreement be assigned under applicable law?",
            "Are deposit terms acceptable?",
            "Are seller authority documents sufficient?",
            "Are there any title/tax/estate issues that must be resolved first?",
            "Does this transaction require any special disclosure?",
        ],
        "do_not_execute_until_reviewed": True,
    }


def build_buyer_teaser_packet(deal: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "packet_type": "buyer_teaser_packet",
        "property_address": deal.get("property_address"),
        "city": deal.get("city"),
        "property_type": deal.get("property_type"),
        "estimated_arv": deal.get("arv"),
        "target_buyer_price": deal.get("target_buyer_price"),
        "estimated_repairs": deal.get("estimated_repairs"),
        "projected_spread": deal.get("projected_spread"),
        "rehab_level": deal.get("rehab_level"),
        "photos_available": bool(deal.get("photos_attached")),
        "disclaimer": "Preliminary opportunity summary. Buyer must complete their own due diligence.",
        "approval_required_before_sending": True,
    }


def build_va_task_packet(deal: Dict[str, Any]) -> Dict[str, Any]:
    tasks = []

    missing_docs = build_missing_documents_checklist(deal)

    for doc in missing_docs:
        tasks.append({
            "task": f"Collect: {doc}",
            "priority": "high",
        })

    tasks.extend([
        {
            "task": "Verify seller contact details",
            "priority": "high",
        },
        {
            "task": "Confirm property photos are uploaded",
            "priority": "medium",
        },
        {
            "task": "Prepare buyer list for matching",
            "priority": "high",
        },
        {
            "task": "Log all communication notes",
            "priority": "high",
        },
    ])

    return {
        "packet_type": "va_task_packet",
        "deal_id": deal.get("id"),
        "property_address": deal.get("property_address"),
        "tasks": tasks,
    }


def build_accounting_packet(deal: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "packet_type": "accounting_packet",
        "deal_id": deal.get("id"),
        "property_address": deal.get("property_address"),
        "purchase_price": deal.get("purchase_price"),
        "target_buyer_price": deal.get("target_buyer_price"),
        "estimated_repairs": deal.get("estimated_repairs"),
        "assignment_fee_target": deal.get("projected_spread"),
        "expected_deposits": deal.get("expected_deposits"),
        "closing_cost_estimate": deal.get("closing_cost_estimate"),
        "notes": [
            "Accounting packet is preliminary.",
            "Final tax treatment requires accountant review.",
        ],
    }


def prepare_deal_packets(deal: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "deal_id": deal.get("id"),
        "property_address": deal.get("property_address"),
        "packets": {
            "seller_offer_summary": build_seller_offer_summary(deal),
            "lawyer_review_packet": build_lawyer_review_packet(deal),
            "buyer_teaser_packet": build_buyer_teaser_packet(deal),
            "va_task_packet": build_va_task_packet(deal),
            "accounting_packet": build_accounting_packet(deal),
        },
        "missing_documents": build_missing_documents_checklist(deal),
        "human_approval_required": True,
        "lawyer_review_required_before_contract": True,
    }
