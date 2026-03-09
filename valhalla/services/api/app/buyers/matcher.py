"""
Module 75: Bulk Disposition Matcher
Match leads to appropriate buyers based on buy-box criteria.
"""


def match_buyers(lead: dict, buyers: list[dict]) -> list[dict]:
    """
    Match lead to buyers based on buy-box criteria.
    
    Currently supports: city and state matching.
    Expand later with zip/radius, asset class, ROI, price range, etc.
    
    Args:
        lead: Lead data dict
            {
                "city": "Denver",
                "state": "CO",
                "arv": 350000,
                ...
            }
        buyers: List of buyer dicts
            [
                {
                    "id": "buyer_123",
                    "name": "John Doe",
                    "buy_box": {"city": "Denver", "state": "CO"}
                }
            ]
    
    Returns:
        list[dict]: Matching buyers
    """
    city = (lead.get("city") or "").lower().strip()
    state = (lead.get("state") or "").lower().strip()

    matches = []
    for b in buyers:
        bb = b.get("buy_box") or {}
        if bb.get("city") and bb.get("city", "").lower().strip() != city:
            continue
        if bb.get("state") and bb.get("state", "").lower().strip() != state:
            continue
        matches.append(b)
    return matches
