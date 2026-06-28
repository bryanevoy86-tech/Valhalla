from typing import Any, Dict, List


SAFE_LANGUAGE_RULES = [
    "Do not imply foreclosure unless verified and legally safe.",
    "Do not threaten legal/tax consequences.",
    "Do not imply guaranteed purchase.",
    "Do not pressure owner.",
    "Do not imply representation by lawyer unless true.",
    "Do not claim official government affiliation.",
]


def determine_outreach_type(property_data: Dict[str, Any]) -> str:
    """
    Determine outreach strategy based on distress score.
    
    - 75+: High distress → soft help messaging
    - 50-74: Moderate distress → general off-market interest
    - 25-49: Light signal → gentle followup
    - <25: Below threshold → do not contact
    """
    distress_score = property_data.get("distress_score", 0)

    if distress_score >= 75:
        return "high_distress_soft_help"
    if distress_score >= 50:
        return "general_off_market_interest"
    if distress_score >= 25:
        return "light_touch_followup"

    return "do_not_contact"


def build_owner_letter(
    owner_name: str,
    property_address: str,
    city: str,
    outreach_type: str,
) -> str:
    """
    Generate owner outreach letter tailored to distress level.
    All language is respectful, non-threatening, and legally compliant.
    """

    if outreach_type == "high_distress_soft_help":
        return f"""
Hi {owner_name},

I hope this letter finds you well.

I came across the property at {property_address} in {city} and wanted to reach out respectfully to see whether you would ever consider selling the property, either now or sometime in the future.

I work with local buyers and property investors, and sometimes we can help owners who would prefer a simple off-market sale without needing to fully list the property publicly.

There is absolutely no pressure or obligation whatsoever. If selling is not something you are considering, please feel free to ignore this message.

If you would be open to a conversation at some point, I would be happy to speak further and see whether there is any fit.

Thank you for your time.
""".strip()

    if outreach_type == "general_off_market_interest":
        return f"""
Hi {owner_name},

My name is Bryan and I wanted to reach out regarding the property at {property_address} in {city}.

I occasionally purchase or work with buyers interested in off-market properties in the area, and I was wondering whether you had ever considered selling the property — now or in the future.

If not, no problem at all. I simply wanted to introduce myself respectfully in case it was something you might consider.

Thank you for your time, and I wish you all the best.
""".strip()

    if outreach_type == "light_touch_followup":
        return f"""
Hi {owner_name},

I hope you are doing well.

I wanted to briefly reach out regarding the property at {property_address} in {city}. If you have ever considered selling the property at some point in the future, I would be happy to have a conversation.

If not, please feel free to disregard this message.

Thank you for your time.
""".strip()

    return """
Outreach blocked. Distress score below threshold or outreach not approved.
""".strip()


def generate_owner_outreach_packet(
    property_record: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate complete owner outreach packet from property intel record.
    
    Includes:
    - Draft letter (tailored to distress level)
    - Safe language rules
    - Recommended delivery methods
    - Human approval requirement flag
    - Outreach gating decision
    """

    distress_analysis = property_record.get("distress_analysis", {})
    property_data = property_record.get("property_data", {})

    distress_score = distress_analysis.get("property_distress_score", 0)
    outreach_allowed = distress_analysis.get("outreach_allowed", False)

    if not outreach_allowed:
        return {
            "allowed": False,
            "reason": "Outreach not allowed by property intelligence engine.",
            "distress_score": distress_score,
        }

    outreach_type = determine_outreach_type({
        "distress_score": distress_score,
    })

    if outreach_type == "do_not_contact":
        return {
            "allowed": False,
            "reason": "Property does not meet outreach threshold.",
            "distress_score": distress_score,
        }

    owner_name = property_data.get("owner_name", "Property Owner")

    letter = build_owner_letter(
        owner_name=owner_name,
        property_address=property_record.get("address"),
        city=property_record.get("city"),
        outreach_type=outreach_type,
    )

    return {
        "allowed": True,
        "outreach_type": outreach_type,
        "distress_score": distress_score,
        "owner_name": owner_name,
        "property_address": property_record.get("address"),
        "city": property_record.get("city"),
        "draft_letter": letter,
        "safe_language_rules": SAFE_LANGUAGE_RULES,
        "requires_human_approval_before_sending": True,
        "recommended_delivery_methods": [
            "handwritten_letter",
            "plain_mail",
            "email_if_lawfully_obtained",
        ],
        "blocked_delivery_methods": [
            "mass_spam",
            "misleading_official_notice_style",
            "aggressive_language",
        ],
    }
