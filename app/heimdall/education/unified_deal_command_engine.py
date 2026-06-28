from typing import Any, Dict, List, Optional

from app.heimdall.education.lead_motivation_engine import score_lead_motivation
from app.heimdall.education.underwriting_engine import underwrite_deal
from app.heimdall.education.buyer_demand_engine import evaluate_buyer_demand
from app.heimdall.education.market_scoring_engine import evaluate_market
from app.heimdall.education.buyer_sourcing_engine import rank_buyers_for_deal

CRITICAL_STOP_FLAGS = [
    "seller_authority_unverified",
    "arv_not_supported",
    "buyer_demand_missing",
    "legal_review_required_but_not_complete",
    "numbers_only_work_best_case",
    "title_issue_unresolved",
    "buyer_pool_too_thin",
    "no_assignment_spread",
    "major_rehab_without_rehab_buyer",
]


def collect_all_red_flags(*results: Dict[str, Any]) -> List[str]:
    flags: List[str] = []
    for result in results:
        for flag in result.get("red_flags", []):
            if flag not in flags:
                flags.append(flag)
        for flag in result.get("expansion_blockers", []):
            if flag not in flags:
                flags.append(flag)
    return flags


def collect_all_missing_data(*results: Dict[str, Any]) -> List[str]:
    missing: List[str] = []
    for result in results:
        for item in result.get("missing_data", []):
            if item not in missing:
                missing.append(item)
    return missing


def has_critical_stop(red_flags: List[str]) -> bool:
    return any(flag in CRITICAL_STOP_FLAGS for flag in red_flags)


def decide_command(
    lead_result: Dict[str, Any],
    underwriting_result: Dict[str, Any],
    buyer_demand_result: Dict[str, Any],
    market_result: Dict[str, Any],
    buyer_match_result: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    red_flags = collect_all_red_flags(
        lead_result,
        underwriting_result,
        buyer_demand_result,
        market_result,
    )
    missing_data = collect_all_missing_data(
        lead_result,
        underwriting_result,
        buyer_demand_result,
        market_result,
    )

    buyer_matches = []
    if buyer_match_result:
        buyer_matches = buyer_match_result.get("recommended_send_list", [])

    if has_critical_stop(red_flags):
        return {
            "command": "PASS_OR_HOLD",
            "reason": "Critical stop flag detected. Do not proceed until resolved.",
            "red_flags": red_flags,
            "missing_data": missing_data,
            "next_steps": [
                "Resolve all critical red flags.",
                "Do not send seller contract.",
                "Do not spend marketing or legal money until blockers are cleared.",
            ],
        }

    if missing_data:
        return {
            "command": "HOLD_MISSING_INFORMATION",
            "reason": "Required information is missing.",
            "red_flags": red_flags,
            "missing_data": missing_data,
            "next_steps": [
                "Collect missing information.",
                "Re-run unified command after data is complete.",
            ],
        }

    if market_result.get("final_decision") != "APPROVED_FOR_TEST_ZONE":
        return {
            "command": "RESEARCH_MARKET_BEFORE_PROCEEDING",
            "reason": "Market is not approved for action yet.",
            "red_flags": red_flags,
            "missing_data": missing_data,
            "next_steps": [
                "Validate market data.",
                "Confirm buyer depth.",
                "Do not expand budget until market score improves.",
            ],
        }

    if buyer_demand_result.get("recommendation") in [
        "DO_NOT_CONTRACT_YET",
        "WEAK_DISPOSITION_CONFIDENCE",
    ]:
        return {
            "command": "BUILD_BUYER_LIST_FIRST",
            "reason": "Buyer demand is too weak to safely contract.",
            "red_flags": red_flags,
            "missing_data": missing_data,
            "next_steps": [
                "Source more buyers.",
                "Get soft interest from qualified buyers.",
                "Re-run buyer demand score.",
            ],
        }

    if not buyer_matches:
        return {
            "command": "SOURCE_OR_MATCH_BUYERS_FIRST",
            "reason": "No matched buyers above minimum threshold.",
            "red_flags": red_flags,
            "missing_data": missing_data,
            "next_steps": [
                "Run buyer sourcing plan.",
                "Add buyer profiles.",
                "Match deal against buyer list.",
            ],
        }

    if underwriting_result.get("recommendation") == "RENEGOTIATE_OR_PASS":
        return {
            "command": "RENEGOTIATE",
            "reason": "Purchase price exceeds Heimdall MAO.",
            "red_flags": red_flags,
            "missing_data": missing_data,
            "next_steps": [
                "Renegotiate seller price.",
                f"Use MAO of ${underwriting_result.get('mao'):,.0f} as maximum.",
                "Do not proceed above MAO without written approval.",
            ],
        }

    if underwriting_result.get("deal_score", 0) >= 85:
        return {
            "command": "STRONG_CANDIDATE_APPROVAL_REQUIRED",
            "reason": "Lead, underwriting, market, and buyer demand are strong.",
            "red_flags": red_flags,
            "missing_data": missing_data,
            "next_steps": [
                "Prepare seller message.",
                "Prepare buyer teaser.",
                "Prepare lawyer review packet.",
                "Request human approval before sending or signing anything.",
            ],
        }

    if underwriting_result.get("deal_score", 0) >= 70:
        return {
            "command": "POSSIBLE_DEAL_MORE_DUE_DILIGENCE",
            "reason": "Deal may work, but confidence is not high enough for clean execution.",
            "red_flags": red_flags,
            "missing_data": missing_data,
            "next_steps": [
                "Validate ARV.",
                "Validate repairs.",
                "Confirm buyer interest.",
                "Tighten offer if possible.",
            ],
        }

    return {
        "command": "PASS_OR_NURTURE",
        "reason": "Deal does not meet current safety threshold.",
        "red_flags": red_flags,
        "missing_data": missing_data,
        "next_steps": [
            "Place seller into follow-up if motivation exists.",
            "Do not contract now.",
        ],
    }


def unified_deal_command(payload: Dict[str, Any]) -> Dict[str, Any]:
    lead = payload.get("lead", {})
    underwriting = payload.get("underwriting", {})
    buyer_demand = payload.get("buyer_demand", {})
    market = payload.get("market", {})
    deal = payload.get("deal", {})
    buyers = payload.get("buyers", [])

    lead_result = score_lead_motivation(lead)
    underwriting_result = underwrite_deal(underwriting)
    buyer_demand_result = evaluate_buyer_demand(buyer_demand)
    market_result = evaluate_market(market)

    buyer_match_result = None
    if buyers:
        buyer_match_result = rank_buyers_for_deal(deal, buyers)

    command_result = decide_command(
        lead_result=lead_result,
        underwriting_result=underwriting_result,
        buyer_demand_result=buyer_demand_result,
        market_result=market_result,
        buyer_match_result=buyer_match_result,
    )

    return {
        "heimdall_command": command_result,
        "subsystem_results": {
            "lead_motivation": lead_result,
            "underwriting": underwriting_result,
            "buyer_demand": buyer_demand_result,
            "market": market_result,
            "buyer_matching": buyer_match_result,
        },
        "human_approval_required": True,
        "legal_review_required_before_contract": True,
        "warning": "Heimdall may recommend next actions, but contracts/legal/tax items require qualified review.",
    }
