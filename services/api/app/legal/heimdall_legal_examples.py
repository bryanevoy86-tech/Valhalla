"""
Heimdall Legal Examples
Sample payloads for Heimdall to use when queuing legal documents.
"""

EXAMPLE_PURCHASE_QUEUE = {
    "approval_id": "deal_123_purchase_agreement",
    "template_key": "purchase_sale_agreement",
    "payload": {
        "date": "2026-04-06",
        "seller_name": "John Seller",
        "buyer_name": "Valhalla Legacy Inc.",
        "property_address": "123 Main St, Winnipeg, MB",
        "purchase_price": "185000",
        "earnest_money": "2500",
        "title_company": "Example Title Co.",
        "inspection_days": "10",
        "closing_date": "2026-04-30",
        "additional_terms": "Subject to lawyer review before final execution."
    },
    "recipients": ["lawyer@example.com"],
    "cc": ["accountant@example.com"],
    "body_intro": "Please review and finalize this draft purchase agreement."
}

EXAMPLE_ASSIGNMENT_QUEUE = {
    "approval_id": "deal_123_assignment_agreement",
    "template_key": "assignment_of_contract",
    "payload": {
        "date": "2026-04-07",
        "your_company": "Valhalla Legacy Inc.",
        "buyer_name": "End Buyer Corp",
        "contract_date": "2026-04-06",
        "property_address": "123 Main St, Winnipeg, MB",
        "assignment_fee": "5000"
    },
    "recipients": ["lawyer@example.com"],
    "cc": ["accountant@example.com"],
    "body_intro": "Please review and finalize this assignment agreement."
}

EXAMPLE_JV_QUEUE = {
    "approval_id": "deal_456_jv_agreement",
    "template_key": "jv_agreement",
    "payload": {
        "your_company": "Valhalla Legacy Inc.",
        "partner_name": "Partner Company Ltd.",
        "property_address": "456 Oak Ave, Toronto, ON",
        "your_split": "60",
        "partner_split": "40",
        "roles": "Valhalla: Sourcing and acquisition\nPartner: Capital and development"
    },
    "recipients": ["lawyer@example.com"],
    "cc": ["partner@example.com", "accountant@example.com"],
    "body_intro": "Please review and finalize this joint venture agreement."
}

EXAMPLE_EARNEST_QUEUE = {
    "approval_id": "deal_123_earnest_money",
    "template_key": "earnest_money_agreement",
    "payload": {
        "buyer_name": "Valhalla Legacy Inc.",
        "property_address": "123 Main St, Winnipeg, MB",
        "earnest_money": "2500",
        "title_company": "Example Title Co."
    },
    "recipients": ["title@exampletitle.com"],
    "cc": ["lawyer@example.com"],
    "body_intro": "Please hold this earnest money deposit per the attached agreement."
}

EXAMPLE_BUYER_NCA_QUEUE = {
    "approval_id": "buyer_789_nca",
    "template_key": "buyer_non_circumvention",
    "payload": {
        "buyer_name": "End Buyer Corp",
        "your_company": "Valhalla Legacy Inc.",
        "agreement_term": "3 years"
    },
    "recipients": ["endbuyer@example.com"],
    "cc": [],
    "body_intro": "Please review and sign this non-circumvention agreement."
}

# Usage example for Heimdall:
# When creating a deal, Heimdall can call:
# POST /api/legal/queue with EXAMPLE_PURCHASE_QUEUE
# Then await user approval
# POST /api/legal/approve/deal_123_purchase_agreement
# Then send via email integration
