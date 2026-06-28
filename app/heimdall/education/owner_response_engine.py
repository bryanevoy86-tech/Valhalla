from typing import Any, Dict


def classify_owner_response(response_text: str) -> Dict[str, Any]:
    """
    Classify owner response into actionable categories.
    
    Categories:
    - DO_NOT_CONTACT: Stop all outreach (critical)
    - INTERESTED: Owner wants to sell (high priority)
    - MAYBE: Owner considering (medium priority)
    - NOT_INTERESTED: Owner not selling (low priority)
    - WRONG_CONTACT: Not the owner (data validation needed)
    - UNCLEAR: Needs manual review
    """
    text = response_text.lower().strip()

    # DO_NOT_CONTACT - Hard stop
    if any(
        phrase in text
        for phrase in [
            "stop",
            "do not contact",
            "don't contact",
            "remove me",
            "unsubscribe",
        ]
    ):
        return {
            "response_type": "DO_NOT_CONTACT",
            "priority": "critical",
            "next_action": "block_future_outreach",
            "lead_interest": "none",
        }

    # INTERESTED - Hot lead
    if any(
        phrase in text
        for phrase in [
            "yes",
            "interested",
            "call me",
            "let's talk",
            "i would sell",
        ]
    ):
        return {
            "response_type": "INTERESTED",
            "priority": "high",
            "next_action": "create_or_update_active_lead",
            "lead_interest": "high",
        }

    # MAYBE - Warm lead
    if any(
        phrase in text
        for phrase in [
            "maybe",
            "depends",
            "what are you offering",
            "how much",
            "possibly",
        ]
    ):
        return {
            "response_type": "MAYBE",
            "priority": "medium",
            "next_action": "follow_up_and_qualify",
            "lead_interest": "medium",
        }

    # NOT_INTERESTED - Cold lead
    if any(
        phrase in text
        for phrase in ["no", "not interested", "not selling"]
    ):
        return {
            "response_type": "NOT_INTERESTED",
            "priority": "low",
            "next_action": "move_to_nurture_or_close",
            "lead_interest": "low",
        }

    # WRONG_CONTACT - Data issue
    if any(
        phrase in text
        for phrase in [
            "wrong person",
            "not mine",
            "i don't own",
            "wrong address",
        ]
    ):
        return {
            "response_type": "WRONG_CONTACT",
            "priority": "medium",
            "next_action": "verify_owner_data",
            "lead_interest": "unknown",
        }

    # UNCLEAR - Manual review
    return {
        "response_type": "UNCLEAR",
        "priority": "medium",
        "next_action": "manual_review_required",
        "lead_interest": "unknown",
    }


def build_owner_response_result(
    property_intel_id: str,
    response_text: str,
    response_channel: str,
) -> Dict[str, Any]:
    """
    Build complete response result with classification and flags.
    """
    classification = classify_owner_response(response_text)
    return {
        "property_intel_id": property_intel_id,
        "response_text": response_text,
        "response_channel": response_channel,
        "classification": classification,
        "human_review_required": classification["response_type"]
        in [
            "UNCLEAR",
            "WRONG_CONTACT",
            "DO_NOT_CONTACT",
        ],
    }
