from typing import Any, Dict, List


def detect_lead_missing_data(lead: Dict[str, Any]) -> List[str]:
    required = [
        "seller_name",
        "property_address",
        "reason_for_selling",
        "timeline_to_sell",
        "asking_price",
        "property_condition",
        "mortgage_or_debt_issue",
        "vacant_or_occupied",
        "seller_responsiveness",
    ]

    return [
        key for key in required
        if key not in lead or lead.get(key) in [None, ""]
    ]


def score_timeline(timeline: str) -> int:
    timeline = timeline.lower()

    if timeline in ["immediately", "asap", "this_week", "within_7_days"]:
        return 20
    if timeline in ["within_30_days", "this_month"]:
        return 16
    if timeline in ["1_to_3_months", "soon"]:
        return 10
    if timeline in ["no_rush", "just_curious", "unknown"]:
        return 3

    return 5


def score_reason(reason: str) -> int:
    reason = reason.lower()

    high_motivation_keywords = [
        "foreclosure",
        "tax arrears",
        "divorce",
        "estate",
        "probate",
        "inherited",
        "vacant",
        "relocation",
        "job loss",
        "debt",
        "cannot afford",
        "repairs too much",
        "bad tenants",
        "tired landlord",
    ]

    medium_keywords = [
        "downsizing",
        "moving",
        "retiring",
        "extra property",
        "rental problem",
        "needs work",
    ]

    for keyword in high_motivation_keywords:
        if keyword in reason:
            return 25

    for keyword in medium_keywords:
        if keyword in reason:
            return 15

    return 5


def score_condition(condition: str) -> int:
    condition = condition.lower()

    if condition in ["major_repairs", "distressed", "unlivable", "fire_damage", "water_damage"]:
        return 15
    if condition in ["needs_work", "dated", "tenant_damage", "rough"]:
        return 12
    if condition in ["average", "livable"]:
        return 6
    if condition in ["excellent", "fully_renovated"]:
        return 1

    return 5


def score_responsiveness(responsiveness: str) -> int:
    responsiveness = responsiveness.lower()

    if responsiveness in ["very_responsive", "answers_fast", "calls_back"]:
        return 15
    if responsiveness in ["somewhat_responsive", "answers_sometimes"]:
        return 9
    if responsiveness in ["slow", "hard_to_reach"]:
        return 4
    if responsiveness in ["ghosting", "no_response"]:
        return 0

    return 5


def detect_motivation_red_flags(lead: Dict[str, Any]) -> List[str]:
    flags = []

    if lead.get("seller_authority_verified") is False:
        flags.append("seller_authority_not_verified")

    if lead.get("asking_price") and lead.get("estimated_arv"):
        asking = float(lead["asking_price"])
        arv = float(lead["estimated_arv"])
        if arv > 0 and asking >= arv * 0.90:
            flags.append("asking_too_close_to_arv")

    if lead.get("timeline_to_sell", "").lower() in ["no_rush", "just_curious"]:
        flags.append("low_urgency")

    if lead.get("seller_responsiveness", "").lower() in ["ghosting", "no_response"]:
        flags.append("seller_unresponsive")

    if lead.get("wants_retail_price", False):
        flags.append("retail_price_expectation")

    if lead.get("refuses_basic_questions", False):
        flags.append("refuses_due_diligence")

    return flags


def score_lead_motivation(lead: Dict[str, Any]) -> Dict[str, Any]:
    missing_data = detect_lead_missing_data(lead)
    red_flags = detect_motivation_red_flags(lead)

    score = 0

    score += score_timeline(str(lead.get("timeline_to_sell", "")))
    score += score_reason(str(lead.get("reason_for_selling", "")))
    score += score_condition(str(lead.get("property_condition", "")))
    score += score_responsiveness(str(lead.get("seller_responsiveness", "")))

    if lead.get("mortgage_or_debt_issue", False):
        score += 10

    if lead.get("vacant_or_occupied", "").lower() == "vacant":
        score += 8

    if lead.get("price_flexible", False):
        score += 7

    score = max(0, min(score, 100))

    if score >= 80:
        lead_lane = "HOT_LEAD_CALL_NOW"
    elif score >= 60:
        lead_lane = "WARM_LEAD_FOLLOW_UP_FAST"
    elif score >= 40:
        lead_lane = "NURTURE_SEQUENCE"
    else:
        lead_lane = "LOW_PRIORITY_OR_DISQUALIFY"

    if "asking_too_close_to_arv" in red_flags and not lead.get("price_flexible", False):
        lead_lane = "LOW_PRIORITY_OR_DISQUALIFY"

    return {
        "motivation_score": score,
        "lead_lane": lead_lane,
        "missing_data": missing_data,
        "red_flags": red_flags,
        "recommended_next_action": get_next_action(lead_lane, red_flags, missing_data),
        "human_approval_required": False,
    }


def get_next_action(lead_lane: str, red_flags: List[str], missing_data: List[str]) -> str:
    if missing_data:
        return "Collect missing seller/property data before underwriting."

    if "seller_authority_not_verified" in red_flags:
        return "Verify seller ownership/authority before offer."

    if lead_lane == "HOT_LEAD_CALL_NOW":
        return "Call seller immediately. Confirm motivation, timeline, condition, authority, and price flexibility."

    if lead_lane == "WARM_LEAD_FOLLOW_UP_FAST":
        return "Follow up within 24 hours. Push for condition details and price flexibility."

    if lead_lane == "NURTURE_SEQUENCE":
        return "Place seller into structured follow-up sequence."

    return "Do not spend major time unless new motivation appears."
