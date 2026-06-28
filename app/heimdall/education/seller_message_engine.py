from typing import Any, Dict


def determine_seller_message_type(command: str) -> str:
    if command == "STRONG_CANDIDATE_APPROVAL_REQUIRED":
        return "soft_offer_or_next_step"
    if command == "RENEGOTIATE":
        return "renegotiation"
    if command == "HOLD_MISSING_INFORMATION":
        return "missing_information_request"
    if command == "POSSIBLE_DEAL_MORE_DUE_DILIGENCE":
        return "due_diligence_followup"
    if command in ["PASS_OR_HOLD", "PASS_OR_NURTURE"]:
        return "nurture_or_polite_hold"
    return "general_followup"


def draft_seller_message(deal: Dict[str, Any], command_result: Dict[str, Any]) -> Dict[str, Any]:
    command = command_result.get("command", "GENERAL_FOLLOWUP")
    message_type = determine_seller_message_type(command)

    seller_name = deal.get("seller_name", "there")
    property_address = deal.get("property_address", "the property")
    recommended_offer = deal.get("recommended_offer")
    missing_documents = deal.get("missing_documents", [])
    reason = command_result.get("reason", "")

    if message_type == "soft_offer_or_next_step":
        message = f"""
Hi {seller_name},

Thanks again for speaking with us about {property_address}.

Based on the information we have so far, this may be a property we can move forward on. Before anything is finalized, we still need to complete our normal review steps, including confirming the property details, reviewing title/tax status, and having the paperwork checked properly.

Our current working number is around ${recommended_offer:,.0f}, subject to final review and approval.

Would you be open to a quick follow-up call so we can confirm the remaining details?
""".strip()

    elif message_type == "renegotiation":
        message = f"""
Hi {seller_name},

I reviewed the numbers again for {property_address}.

Based on the repairs, resale/rental assumptions, and the risk involved, we would not be able to safely move forward at the current price. To make this work, we would need to be closer to ${recommended_offer:,.0f}, subject to final review.

I understand that may not be where you hoped to be, but I wanted to be upfront rather than waste your time.

Would you be open to discussing that range?
""".strip()

    elif message_type == "missing_information_request":
        missing_text = "\n".join([f"- {item}" for item in missing_documents]) if missing_documents else "- property details"

        message = f"""
Hi {seller_name},

Before we can give you a proper answer on {property_address}, we need a few more details.

Could you please help confirm:

{missing_text}

Once we have that, we can review the property properly and let you know the next step.
""".strip()

    elif message_type == "due_diligence_followup":
        message = f"""
Hi {seller_name},

We are still reviewing {property_address}. The property may be a fit, but we need to complete a bit more due diligence before making any firm decision.

The main thing is making sure the numbers, repairs, and paperwork all make sense before anyone moves forward.

Can we confirm a few more details today?
""".strip()

    elif message_type == "nurture_or_polite_hold":
        message = f"""
Hi {seller_name},

Thanks for sharing the information about {property_address}.

At the moment, it does not look like we can safely move forward based on the current numbers and details. That said, if anything changes with your timeline, price, or situation, we would be happy to review it again.

I appreciate your time.
""".strip()

    else:
        message = f"""
Hi {seller_name},

I wanted to follow up about {property_address} and see if you are still considering your options.

If you are, we can review the details and see whether there is a way to make something work.
""".strip()

    return {
        "message_type": message_type,
        "command_used": command,
        "seller_name": seller_name,
        "property_address": property_address,
        "reason": reason,
        "draft_message": message,
        "requires_human_approval_before_sending": True,
        "legal_warning": "Do not send binding legal language or contract terms without approval and lawyer-reviewed templates.",
    }
