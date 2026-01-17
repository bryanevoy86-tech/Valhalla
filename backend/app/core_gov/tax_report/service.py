"""P-TAXREP-1: Tax summary report service."""
from __future__ import annotations

from typing import Any, Dict

def summary(month: str) -> Dict[str, Any]:
    """
    Generate tax summary report for a month (YYYY-MM).
    
    Safe-calls: ledger_light, tax_map, tax_buckets
    """
    report = {
        "month": month,
        "by_bucket": {},
        "unmapped": [],
    }
    
    # Safe-call to ledger_light
    try:
        from ..ledger_light import store as ledger_store
        transactions = ledger_store.list_items()
        
        # Safe-call to tax_map
        tax_map = {}
        try:
            from ..tax_map import store as taxmap_store
            tax_map = taxmap_store.get_map()
        except:
            pass
        
        for txn in transactions:
            if txn.get("date", "").startswith(month):
                category = txn.get("category", "")
                amount = float(txn.get("amount", 0))
                
                if category in tax_map:
                    bucket = tax_map[category]
                    if bucket not in report["by_bucket"]:
                        report["by_bucket"][bucket] = 0
                    report["by_bucket"][bucket] += abs(amount)
                else:
                    report["unmapped"].append({
                        "category": category,
                        "amount": amount,
                    })
    except:
        pass
    
    return report
