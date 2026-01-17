from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


Status = Literal["open", "purchased", "skipped", "archived"]
Priority = Literal["low", "normal", "high", "critical"]
Category = Literal["groceries", "household", "kids", "clothing", "home", "tools", "auto", "health", "other"]


class ShoppingItemCreate(BaseModel):
    name: str
    category: Category = "other"
    status: Status = "open"
    priority: Priority = "normal"

    desired_by: str = ""              # "YYYY-MM-DD" optional
    qty: float = 1.0
    unit: str = "count"               # free-text to avoid unit conflicts
    est_unit_cost: float = 0.0
    currency: str = "CAD"

    preferred_store: str = ""
    preferred_brand: str = ""

    # optional linkage
    inventory_item_id: str = ""       # if tied to /core/inventory item
    source: str = "manual"            # manual / inventory / budget / other

    tags: List[str] = Field(default_factory=list)
    notes: str = ""
    meta: Dict[str, Any] = Field(default_factory=dict)


class ShoppingItemRecord(BaseModel):
    id: str
    name: str
    category: Category
    status: Status
    priority: Priority
    desired_by: str = ""
    qty: float
    unit: str
    est_unit_cost: float
    currency: str
    preferred_store: str = ""
    preferred_brand: str = ""
    inventory_item_id: str = ""
    source: str = "manual"
    tags: List[str] = Field(default_factory=list)
    notes: str = ""
    meta: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class ShoppingListResponse(BaseModel):
    items: List[ShoppingItemRecord]
