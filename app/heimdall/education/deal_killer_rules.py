HEIMDALL_DEAL_KILLER_RULES = {
    "prime_warning": (
        "If a deal requires ignored risks, missing paperwork, unrealistic assumptions, "
        "or unverified legal authority to be profitable, Heimdall must stop the user."
    ),
    "title_and_authority_killers": [
        {
            "flag": "seller_authority_unverified",
            "severity": "critical",
            "action": "block_until_verified",
            "message": "Seller authority is not verified. Do not contract until ownership/authority is confirmed.",
        },
        {
            "flag": "estate_or_probate_unclear",
            "severity": "critical",
            "action": "legal_review_required",
            "message": "Estate/probate issue detected. Lawyer review required before offer or contract.",
        },
        {
            "flag": "multiple_owners_not_all_confirmed",
            "severity": "critical",
            "action": "block_until_all_owners_confirmed",
            "message": "All owners must be identified and willing before proceeding.",
        },
        {
            "flag": "tax_lien_or_arrears_unknown",
            "severity": "high",
            "action": "investigate_before_offer",
            "message": "Tax arrears/lien status unknown. Verify before calculating max offer.",
        },
    ],
    "number_killers": [
        {
            "flag": "arv_not_supported",
            "severity": "critical",
            "action": "block_recommendation",
            "message": "ARV is unsupported. Heimdall cannot recommend buy/contract.",
        },
        {
            "flag": "repair_budget_guess",
            "severity": "high",
            "action": "require_repair_validation",
            "message": "Repair budget is a guess. Require contractor estimate or conservative repair model.",
        },
        {
            "flag": "profit_under_minimum",
            "severity": "high",
            "action": "recommend_pass_or_renegotiate",
            "message": "Projected profit is under minimum threshold. Pass or renegotiate.",
        },
        {
            "flag": "rent_assumption_unverified",
            "severity": "high",
            "action": "require_rent_validation",
            "message": "Rent assumption is unverified. Validate against CMHC/local listings before BRRRR decision.",
        },
    ],
    "contract_killers": [
        {
            "flag": "no_lawyer_review_for_new_template",
            "severity": "critical",
            "action": "block_use",
            "message": "New or modified legal template must be reviewed by a lawyer before use.",
        },
        {
            "flag": "assignment_language_unclear",
            "severity": "critical",
            "action": "legal_review_required",
            "message": "Assignment language unclear. Lawyer review required.",
        },
        {
            "flag": "deposit_terms_unclear",
            "severity": "high",
            "action": "clarify_before_signing",
            "message": "Deposit terms are unclear. Do not sign until corrected.",
        },
    ],
    "market_killers": [
        {
            "flag": "buyer_demand_missing",
            "severity": "critical",
            "action": "hold_until_buyer_validation",
            "message": "No verified buyer demand. Do not wholesale without exit confidence.",
        },
        {
            "flag": "high_hazard_or_insurance_risk",
            "severity": "high",
            "action": "insurance_quote_required",
            "message": "Hazard/insurance risk detected. Insurance quote required before offer.",
        },
        {
            "flag": "days_on_market_rising_fast",
            "severity": "medium",
            "action": "tighten_offer",
            "message": "Market liquidity weakening. Lower offer or require stronger spread.",
        },
    ],
    "beginner_bias_warnings": [
        "Do not force a deal because you need money.",
        "Do not trust seller numbers without verification.",
        "Do not assume ARV from active listings only.",
        "Do not ignore repairs you cannot see.",
        "Do not count profit before closing.",
        "Do not skip legal review to save money.",
        "Do not expand zones before the current zone has repeatable KPIs.",
    ],
}
