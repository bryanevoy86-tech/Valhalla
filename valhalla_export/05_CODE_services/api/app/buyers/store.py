"""
Module 67: Buyers Directory Store
In-memory storage for buyer profiles with contact info and buy-box criteria.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional


@dataclass
class Buyer:
    """Buyer profile with contact and buy-box criteria."""
    id: str
    name: str
    email: str | None = None
    phone: str | None = None
    buy_box: dict | None = None  # criteria (city, state, price range, etc.)


class BuyerStore:
    """In-memory store for buyer profiles."""
    
    def __init__(self) -> None:
        """Initialize empty buyer store."""
        self._buyers: Dict[str, Buyer] = {}

    def upsert(self, b: Buyer) -> Buyer:
        """
        Insert or update buyer.
        
        Args:
            b: Buyer object
            
        Returns:
            Buyer: The upserted buyer
        """
        self._buyers[b.id] = b
        return b

    def get(self, buyer_id: str) -> Optional[Buyer]:
        """
        Get buyer by ID.
        
        Args:
            buyer_id: Buyer ID
            
        Returns:
            Optional[Buyer]: Buyer if found, None otherwise
        """
        return self._buyers.get(buyer_id)

    def list(self) -> List[dict]:
        """
        List all buyers.
        
        Returns:
            List[dict]: List of buyer dictionaries
        """
        return [asdict(b) for b in self._buyers.values()]


# Global buyer store
BUYERS = BuyerStore()
