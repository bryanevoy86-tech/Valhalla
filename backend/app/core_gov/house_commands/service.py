"""P-HOUSECMD-1: Household command service (v1 NLP parser)."""
from __future__ import annotations

from typing import Any, Dict

def execute(text: str) -> Dict[str, Any]:
    """
    Parse and execute a household command.
    v1: Simple keyword-based parser.
    
    Safe-calls: journal (safe)
    """
    text_lower = text.lower().strip()
    intent = "unknown"
    note_text = ""
    action = {}
    
    # Simple intent detection
    if any(w in text_lower for w in ["remind", "remember", "note", "add", "brain dump"]):
        intent = "journal_add"
        note_text = text
        try:
            from ..journal import store as journal_store
            action["result"] = journal_store.add(text, tags=["voice"])
        except:
            action["result"] = {"status": "safe-call skipped"}
    
    elif any(w in text_lower for w in ["bill", "pay", "upcoming", "due"]):
        intent = "bills_check"
        action["intent_detail"] = "Check upcoming bills"
    
    elif any(w in text_lower for w in ["balance", "account", "cash", "money"]):
        intent = "balance_check"
        action["intent_detail"] = "Check balance or runway"
    
    elif any(w in text_lower for w in ["receipt", "expense", "purchase", "bought"]):
        intent = "receipt_add"
        action["intent_detail"] = "Add receipt to vault"
    
    elif any(w in text_lower for w in ["tax", "deduct", "cra"]):
        intent = "tax_check"
        action["intent_detail"] = "View tax summary"
    
    else:
        intent = "unrecognized"
    
    return {
        "intent": intent,
        "text": text,
        "action": action,
    }
