from typing import Any, Dict, List
from datetime import datetime


DEAL_STATES = [
    "NEW_LEAD",
    "MOTIVATION_REVIEW",
    "UNDERWRITING_REVIEW",
    "MARKET_REVIEW",
    "BUYER_DEMAND_REVIEW",
    "BUYER_SOURCING",
    "NEGOTIATION",
    "LAWYER_REVIEW",
    "APPROVAL_REQUIRED",
    "BUYER_OUTREACH",
    "CONTRACT_PENDING",
    "CLOSED",
    "PASS",
    "NURTURE",
    "DEAD",
]

ALLOWED_TRANSITIONS = {
    "NEW_LEAD": ["MOTIVATION_REVIEW", "DEAD"],
    "MOTIVATION_REVIEW": ["UNDERWRITING_REVIEW", "NURTURE", "PASS"],
    "UNDERWRITING_REVIEW": ["MARKET_REVIEW", "NEGOTIATION", "PASS"],
    "MARKET_REVIEW": ["BUYER_DEMAND_REVIEW", "PASS"],
    "BUYER_DEMAND_REVIEW": ["BUYER_SOURCING", "LAWYER_REVIEW", "PASS"],
    "BUYER_SOURCING": ["BUYER_OUTREACH", "PASS"],
    "NEGOTIATION": ["UNDERWRITING_REVIEW", "PASS", "NURTURE"],
    "LAWYER_REVIEW": ["APPROVAL_REQUIRED", "PASS"],
    "APPROVAL_REQUIRED": ["BUYER_OUTREACH", "CONTRACT_PENDING", "PASS"],
    "BUYER_OUTREACH": ["CONTRACT_PENDING", "NEGOTIATION", "PASS"],
    "CONTRACT_PENDING": ["CLOSED", "PASS"],
    "CLOSED": [],
    "PASS": ["NURTURE", "DEAD"],
    "NURTURE": ["MOTIVATION_REVIEW", "DEAD"],
    "DEAD": [],
}

COMMAND_TO_STATE = {
    "HOLD_MISSING_INFORMATION": "MOTIVATION_REVIEW",
    "RESEARCH_MARKET_BEFORE_PROCEEDING": "MARKET_REVIEW",
    "BUILD_BUYER_LIST_FIRST": "BUYER_SOURCING",
    "SOURCE_OR_MATCH_BUYERS_FIRST": "BUYER_SOURCING",
    "RENEGOTIATE": "NEGOTIATION",
    "STRONG_CANDIDATE_APPROVAL_REQUIRED": "LAWYER_REVIEW",
    "POSSIBLE_DEAL_MORE_DUE_DILIGENCE": "UNDERWRITING_REVIEW",
    "PASS_OR_HOLD": "PASS",
    "PASS_OR_NURTURE": "NURTURE",
}


def can_transition(current_state: str, next_state: str) -> bool:
    """Check if transition from current_state to next_state is allowed."""
    return next_state in ALLOWED_TRANSITIONS.get(current_state, [])


def recommend_next_state(current_state: str, command_result: Dict[str, Any]) -> Dict[str, Any]:
    """Based on Heimdall command, recommend the next state."""
    command = command_result.get("command")
    recommended_state = COMMAND_TO_STATE.get(command, current_state)
    allowed = can_transition(current_state, recommended_state)

    if not allowed and recommended_state != current_state:
        return {
            "allowed": False,
            "current_state": current_state,
            "recommended_state": recommended_state,
            "reason": "Transition is not allowed from current state.",
            "allowed_transitions": ALLOWED_TRANSITIONS.get(current_state, []),
        }

    return {
        "allowed": True,
        "current_state": current_state,
        "recommended_state": recommended_state,
        "reason": f"Heimdall command maps to {recommended_state}.",
        "command": command,
    }


def advance_deal_state(
    deal: Dict[str, Any],
    command_result: Dict[str, Any],
    advanced_by: str = "heimdall",
) -> Dict[str, Any]:
    """Advance deal to next state based on command result. Returns updated deal."""
    current_state = deal.get("state", "NEW_LEAD")
    recommendation = recommend_next_state(current_state, command_result)

    if not recommendation["allowed"]:
        return {
            "deal_id": deal.get("id"),
            "state_changed": False,
            "error": recommendation,
            "human_review_required": True,
        }

    next_state = recommendation["recommended_state"]

    history_entry = {
        "from_state": current_state,
        "to_state": next_state,
        "command": command_result.get("command"),
        "reason": command_result.get("reason"),
        "advanced_by": advanced_by,
        "timestamp": datetime.utcnow().isoformat(),
    }

    existing_history: List[Dict[str, Any]] = deal.get("state_history", [])

    updated_deal = {
        **deal,
        "state": next_state,
        "last_command": command_result.get("command"),
        "last_state_update": datetime.utcnow().isoformat(),
        "state_history": existing_history + [history_entry],
    }

    return {
        "deal_id": deal.get("id"),
        "state_changed": current_state != next_state,
        "previous_state": current_state,
        "new_state": next_state,
        "updated_deal": updated_deal,
        "human_review_required": next_state in [
            "LAWYER_REVIEW",
            "APPROVAL_REQUIRED",
            "CONTRACT_PENDING",
        ],
    }


def get_pipeline_requirements(state: str) -> Dict[str, Any]:
    """Return required checklist items for a given pipeline state."""
    requirements = {
        "NEW_LEAD": ["Basic seller/property info"],
        "MOTIVATION_REVIEW": ["Seller motivation score", "Authority check", "Timeline"],
        "UNDERWRITING_REVIEW": ["ARV", "Repairs", "MAO", "Spread", "Risk flags"],
        "MARKET_REVIEW": ["Market score", "Buyer pool", "Distressed inventory"],
        "BUYER_DEMAND_REVIEW": ["Buyer demand score", "Recent investor activity"],
        "BUYER_SOURCING": ["Buyer sourcing plan", "Buyer profiles", "Match scores"],
        "NEGOTIATION": ["Seller message draft", "Updated offer range", "Approval"],
        "LAWYER_REVIEW": ["Lawyer packet", "Draft terms", "Authority docs"],
        "APPROVAL_REQUIRED": ["Owner approval", "Legal clearance", "Final risk summary"],
        "BUYER_OUTREACH": ["Approved buyer messages", "Buyer teaser packet"],
        "CONTRACT_PENDING": ["Signed docs", "Deposit terms", "Closing checklist"],
        "CLOSED": ["Final accounting", "Outcome tracking", "Learning feedback"],
        "PASS": ["Pass reason logged"],
        "NURTURE": ["Follow-up date", "Nurture sequence"],
        "DEAD": ["Dead reason logged"],
    }

    return {
        "state": state,
        "requirements": requirements.get(state, []),
    }
