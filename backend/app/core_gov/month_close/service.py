"""P-MONTHCLOSE-1: Month close service."""
from __future__ import annotations

from typing import Any, Dict

from . import store

def close(month: str, notes: str = "") -> Dict[str, Any]:
    """
    Generate a month close snapshot.
    
    Safe-calls: budget_obligations (safe), ledger_light (safe)
    """
    # Safely gather summary from ledger
    ledger_summary = {"income": 0, "expense": 0, "transfers": 0}
    try:
        from ..ledger_light import store as ledger_store
        transactions = ledger_store.list_items()
        for txn in transactions:
            if txn.get("date", "").startswith(month):
                amt = float(txn.get("amount", 0))
                if txn.get("type") == "income":
                    ledger_summary["income"] += abs(amt)
                elif txn.get("type") == "expense":
                    ledger_summary["expense"] += abs(amt)
                elif txn.get("type") == "transfer":
                    ledger_summary["transfers"] += abs(amt)
    except:
        pass
    
    snapshot = {
        **ledger_summary,
        "notes": notes,
    }
    
    return store.create(month, snapshot)

def list_snapshots() -> list[Dict[str, Any]]:
    """List all month close snapshots."""
    return store.list_items()
