from typing import Any, Dict, List

def run_red_flags(data: Dict[str, Any] | None = None) -> Dict[str, Any]:
    data = data or {}
    flags: List[str] = []

    if data.get("missing_receipts"):
        flags.append("Missing receipts")
    if data.get("unclassified_income"):
        flags.append("Unclassified income")
    if data.get("personal_and_business_mixed"):
        flags.append("Possible commingling of funds")
    if data.get("owner_draw") and data.get("pre_approval_mode", True):
        flags.append("Owner draw during pre-approval / protected mode")
    if data.get("uncategorized_expense_count", 0) > 0:
        flags.append("Uncategorized expenses present")

    risk = "LOW"
    if len(flags) >= 1:
        risk = "MEDIUM"
    if len(flags) >= 3:
        risk = "HIGH"

    return {
        "risk": risk,
        "flags": flags,
        "count": len(flags),
    }

def calculate_risk_score(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate overall risk score based on red flags.
    
    Returns:
        Dictionary with risk assessment
    """
    flags = run_red_flags(data)
    
    risk_level = "LOW"
    if len(flags) >= 3:
        risk_level = "MEDIUM"
    if len(flags) >= 6:
        risk_level = "HIGH"
    
    return {
        "flag_count": len(flags),
        "risk_level": risk_level,
        "flags": flags,
        "requires_review": len(flags) > 0,
        "audit_ready": len(flags) == 0
    }

def review_compliance(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Full compliance review with red flag analysis.
    
    Returns:
        Comprehensive compliance assessment
    """
    flags = run_red_flags(data)
    risk = calculate_risk_score(data)
    
    return {
        "status": "COMPLIANT" if not flags else "REVIEW_REQUIRED",
        "red_flags": flags,
        "risk_assessment": risk,
        "timestamp": data.get("timestamp", "unknown"),
        "actions_required": len(flags) > 0
    }
