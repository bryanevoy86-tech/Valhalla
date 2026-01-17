"""Smart ledger add with auto-categorization using ledger rules."""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

# Safe import
try:
    from . import store as ledger_store
except ImportError:
    ledger_store = None

try:
    from ..ledger_rules import service as rules_service
except ImportError:
    rules_service = None


def smart_create(
    date: str,
    kind: str,
    amount: float,
    description: str,
    account_id: str,
    category: Optional[str] = None,
    notes: str = ""
) -> Dict[str, Any]:
    """Create ledger entry with auto-categorization via ledger rules.
    
    Args:
        date: Transaction date (YYYY-MM-DD)
        kind: "income" or "expense"
        amount: Transaction amount
        description: Transaction description
        account_id: Account identifier
        category: Override auto-category (optional)
        notes: Additional notes
    
    Returns:
        Created ledger entry with resolved category
    """
    # Auto-categorize if no category provided
    if not category and rules_service:
        try:
            category = rules_service.apply(description)
        except Exception:
            category = ""
    
    # Build entry
    entry = {
        "id": "led_" + uuid.uuid4().hex[:10],
        "date": date,
        "kind": kind,
        "amount": float(amount),
        "description": description,
        "category": category or "uncategorized",
        "account_id": account_id,
        "notes": notes,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Store if available
    if ledger_store:
        try:
            items = ledger_store.list_items()
            items.append(entry)
            ledger_store.save_items(items)
        except Exception:
            pass
    
    return entry
