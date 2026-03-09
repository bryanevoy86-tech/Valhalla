"""QuickBooks sync - stub for accounting integration.

Today: Just queue the revenue entries.
Later: Implement actual QuickBooks API calls.
"""


def sync_revenue(entry) -> dict:
    """
    Queue a revenue entry for QuickBooks sync.
    
    Args:
        entry: RevenueEntry model instance
    
    Returns:
        dict with queue status
    """
    return {
        "status": "queued",
        "entry_id": entry.id,
        "engine": entry.engine,
        "amount": entry.amount,
        "message": "Revenue entry queued for QuickBooks sync"
    }


def sync_contract(contract) -> dict:
    """
    Queue a contract for QuickBooks sync.
    
    Args:
        contract: Contract model instance
    
    Returns:
        dict with queue status
    """
    return {
        "status": "queued",
        "contract_id": contract.id,
        "amount": 0,  # TODO: Calculate from contract
        "message": "Contract queued for QuickBooks sync"
    }


def get_sync_queue_status() -> dict:
    """Get status of QuickBooks sync queue."""
    # TODO: Implement actual queue checking
    return {
        "status": "stub",
        "queued_items": 0,
        "last_sync": None,
        "next_sync_due": None,
        "message": "QuickBooks sync not yet implemented"
    }


def process_sync_queue() -> dict:
    """Process queued items for QuickBooks sync."""
    # TODO: Implement actual QuickBooks API calls
    return {
        "status": "stub",
        "items_processed": 0,
        "items_failed": 0,
        "message": "QuickBooks sync not yet implemented"
    }
