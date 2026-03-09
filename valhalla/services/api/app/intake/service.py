"""Deal intake service - persist incoming deals."""
from uuid import uuid4
from app.intake.models import Deal


def create_deal(source: str, payload: dict) -> dict:
    """
    Create a deal record from external source.
    
    Args:
        source: Source of deal (zillow, mls, etc)
        payload: Raw data from source
    
    Returns:
        Deal dict with id and created_at
    """
    deal = Deal(
        id=f"deal_{uuid4().hex[:12]}",
        source=source,
        payload=payload
    )
    
    # In real implementation, would save to database
    return {
        "id": deal.id,
        "source": deal.source,
        "created_at": deal.created_at.isoformat()
    }


def get_deal(deal_id: str) -> dict:
    """Get deal by ID."""
    return {
        "id": deal_id,
        "source": "unknown",
        "payload": {}
    }
