from typing import Any, Dict, List, Optional


def build_property_research_plan(
    address: str,
    city: str,
    province_or_state: Optional[str] = None,
    country: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Build research plan for a property address.
    Defines what research steps need to be taken to verify ownership and distress.
    """
    return {
        "address": address,
        "city": city,
        "province_or_state": province_or_state,
        "country": country,
        "research_steps": [
            {
                "step": 1,
                "name": "Assessment Roll Lookup",
                "source": "Winnipeg Assessment Roll",
                "purpose": "Verify current owner, property details, assessed value",
                "required": True,
            },
            {
                "step": 2,
                "name": "Tax Delinquency Check",
                "source": "Tax Authority Records",
                "purpose": "Identify overdue taxes, delinquency timeline",
                "required": True,
            },
            {
                "step": 3,
                "name": "Foreclosure & Lien Search",
                "source": "Court Records / Title Search",
                "purpose": "Identify liens, foreclosure status, bank involvement",
                "required": True,
            },
            {
                "step": 4,
                "name": "Historical Sales & Comps",
                "source": "MLS / Historical Sales Data",
                "purpose": "Estimate ARV, identify price trends",
                "required": False,
            },
            {
                "step": 5,
                "name": "Property Condition Assessment",
                "source": "Public Records / City Inspections",
                "purpose": "Identify code violations, structural issues",
                "required": False,
            },
        ],
        "research_required": True,
        "estimated_research_time_minutes": 15,
    }


def score_property_distress_signal(property_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Score distress signals from property data.
    Returns distress score, lane assignment, and gating decisions.
    """
    distress_score = 0
    signals = []
    
    # Tax delinquency signals
    if property_data.get("is_tax_delinquent", False):
        overdue = property_data.get("tax_overdue_amount", 0)
        years = property_data.get("years_tax_delinquent", 0)
        distress_score += 40
        signals.append(f"Tax delinquent: ${overdue} overdue for {years} years")
    
    # Foreclosure signals
    if property_data.get("in_foreclosure", False):
        stage = property_data.get("foreclosure_stage", "unknown")
        distress_score += 50
        signals.append(f"In foreclosure: {stage}")
    
    # Lien signals
    if property_data.get("has_liens", False):
        lien_count = property_data.get("lien_count", 0)
        distress_score += 30
        signals.append(f"Liens on property: {lien_count}")
    
    # Bank owned signal
    if property_data.get("is_bank_owned", False):
        distress_score += 35
        signals.append("Bank owned (REO)")
    
    # Property condition
    condition = property_data.get("property_condition", "")
    if condition in ["poor", "fair"]:
        distress_score += 20
        signals.append(f"Poor property condition: {condition}")
    
    # Capped at 100
    distress_score = min(distress_score, 100)
    
    # Lane assignment
    if distress_score >= 70:
        lane = "HOT_LEAD"
    elif distress_score >= 40:
        lane = "WARM_LEAD"
    elif distress_score >= 20:
        lane = "RESEARCH_MORE"
    else:
        lane = "PASS"
    
    # Determine if outreach is allowed
    ownership_verified = not property_data.get("ownership_verification_required", True)
    outreach_allowed = (
        distress_score >= 50 and
        not property_data.get("is_bank_owned", False) and
        not property_data.get("in_foreclosure", False)
    )
    
    return {
        "property_distress_score": distress_score,
        "lane": lane,
        "signals": signals,
        "ownership_verification_required": not ownership_verified,
        "outreach_allowed": outreach_allowed,
        "research_complete": property_data.get("research_complete", False),
    }


def build_owner_outreach_research_packet(
    address_payload: Dict[str, Any],
    property_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Build complete research packet after data is collected.
    Combines research plan results with distress analysis.
    """
    research_plan = build_property_research_plan(
        address=address_payload.get("address"),
        city=address_payload.get("city"),
        province_or_state=address_payload.get("province_or_state"),
        country=address_payload.get("country"),
    )
    
    distress_analysis = score_property_distress_signal(property_data)
    
    owner_info = property_data.get("owner_info", {})
    
    return {
        "address_payload": address_payload,
        "research_plan": research_plan,
        "property_data": property_data,
        "distress_analysis": distress_analysis,
        "owner_contact_info": {
            "owner_name": owner_info.get("owner_name", "Unknown"),
            "owner_type": owner_info.get("owner_type", "unknown"),  # individual, company, trust, estate
            "mailing_address": owner_info.get("mailing_address", ""),
            "phone": owner_info.get("phone"),
            "email": owner_info.get("email"),
        },
        "outreach_recommendation": (
            "CONTACT_IMMEDIATELY" if distress_analysis.get("lane") == "HOT_LEAD"
            else "RESEARCH_BEFORE_CONTACT" if distress_analysis.get("lane") == "WARM_LEAD"
            else "MONITOR_OR_SKIP"
        ),
        "distress_reason": (
            owner_info.get("distress_reason", "")
            or distress_analysis.get("signals", ["Unknown distress"])[0]
        ),
    }
