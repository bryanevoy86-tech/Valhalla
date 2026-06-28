from app.heimdall.knowledge.trusted_sources import TRUSTED_KNOWLEDGE_SOURCES
from app.heimdall.knowledge.deal_decision_rules import DEAL_DECISION_RULES


def load_heimdall_knowledge_base() -> dict:
    """
    Loads Heimdall's trusted source registry and base decision rules.

    This does NOT scrape sources automatically.
    It registers trusted sources and baseline rules so future ingestion,
    research, scoring, and AI reasoning use reliable references first.
    """

    return {
        "trusted_sources": TRUSTED_KNOWLEDGE_SOURCES,
        "deal_decision_rules": DEAL_DECISION_RULES,
        "status": "loaded",
        "warning": (
            "This is a trusted-source registry and baseline decision framework. "
            "Live ingestion, API pulls, market scoring, and continuous learning "
            "must be built as separate modules."
        ),
    }
