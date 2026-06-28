from app.heimdall.education.source_registry import HEIMDALL_SOURCE_REGISTRY
from app.heimdall.education.error_catcher_rules import HEIMDALL_ERROR_CATCHER_RULES
from app.heimdall.education.compliance_sources import HEIMDALL_COMPLIANCE_SOURCES
from app.heimdall.education.deal_killer_rules import HEIMDALL_DEAL_KILLER_RULES


def load_heimdall_education_layer() -> dict:
    """
    Loads Heimdall's pre-launch education spine.

    This provides:
    - Trusted sources for market data, property data, and economic indicators
    - Compliance and legal sources for regulatory requirements
    - Error-catcher rules that flag bad assumptions
    - Deal killer rules that block high-risk decisions
    - Deal scoring weights and recommendation bands
    - Human approval gates for high-risk decisions

    This does NOT automatically scrape or ingest data.
    This does NOT replace professionals (lawyers, accountants, brokers, appraisers, insurance).
    All high-risk decisions require human approval.
    """
    return {
        "status": "loaded",
        "purpose": "Pre-launch education spine for Heimdall decision support.",
        "trusted_sources": HEIMDALL_SOURCE_REGISTRY,
        "compliance_sources": HEIMDALL_COMPLIANCE_SOURCES,
        "error_catcher_rules": HEIMDALL_ERROR_CATCHER_RULES,
        "deal_killer_rules": HEIMDALL_DEAL_KILLER_RULES,
        "limits": [
            "This does not replace lawyers, accountants, brokers, appraisers, or licensed insurance professionals.",
            "This registry does not scrape or ingest automatically yet.",
            "All high-risk decisions require human approval.",
        ],
    }
