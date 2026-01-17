"""Bridge house inventory low items to shopping list."""
from __future__ import annotations
from typing import Any, Dict, List

# Safe imports
try:
    from . import service as inventory_service
except ImportError:
    inventory_service = None

try:
    from ..shopping_list.service import add_item as add_to_shopping
except ImportError:
    add_to_shopping = None


def push_low_to_shopping() -> Dict[str, Any]:
    """Convert low inventory items to shopping list items.
    
    Returns:
        Dict with created shopping items count
    """
    created = 0
    
    if not inventory_service:
        return {"created": 0}
    
    try:
        # Get low inventory items
        low_items = inventory_service.list_low()
        
        if add_to_shopping:
            for item in low_items:
                try:
                    # Convert to shopping item
                    shopping_item = {
                        "name": item.get("name", ""),
                        "qty": item.get("qty", 1),
                        "unit": item.get("unit", ""),
                        "notes": item.get("notes", "") or "Reorder needed"
                    }
                    add_to_shopping(**shopping_item)
                    created += 1
                except Exception:
                    pass  # Skip failed conversions
    except Exception:
        pass
    
    return {"created": created}
