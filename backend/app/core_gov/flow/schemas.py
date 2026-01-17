from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


ItemType = Literal["consumable", "household", "kids", "pet", "health", "other"]
Urgency = Literal["low", "medium", "high", "critical"]
Status = Literal["active", "paused", "archived"]


class SupplyItemCreate(BaseModel):
    name: str                         # "Toilet Paper", "Milk"
    item_type: ItemType = "household"
    status: Status = "active"
    preferred_brand: str = ""
    preferred_size: str = ""          # "12-pack", "4L"
    est_unit_cost: float = 0.0
    reorder_point: float = 1.0        # when <= reorder_point -> needs refill
    target_level: float = 3.0         # restock up to this level
    cadence_days: int = 14            # expected usage cycle
    store_pref: str = ""              # "Costco", "Walmart"
    tags: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)


class SupplyItemRecord(BaseModel):
    id: str
    name: str
    item_type: ItemType
    status: Status
    preferred_brand: str = ""
    preferred_size: str = ""
    est_unit_cost: float = 0.0
    reorder_point: float = 1.0
    target_level: float = 3.0
    cadence_days: int = 14
    store_pref: str = ""
    tags: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class InventoryUpdate(BaseModel):
    item_id: str
    current_level: float
    urgency: Urgency = "medium"
    note: str = ""


class InventoryState(BaseModel):
    item_id: str
    current_level: float
    urgency: Urgency
    note: str = ""
    updated_at: datetime


class ShoppingAddRequest(BaseModel):
    item_id: str
    qty: float = 1.0
    urgency: Urgency = "medium"
    note: str = ""


class ShoppingItem(BaseModel):
    id: str
    item_id: str
    name: str
    qty: float
    est_cost: float = 0.0
    urgency: Urgency
    status: Literal["open", "done", "canceled"] = "open"
    note: str = ""
    created_at: datetime
    updated_at: datetime


class SupplyListResponse(BaseModel):
    items: List[SupplyItemRecord]


class ShoppingListResponse(BaseModel):
    items: List[ShoppingItem]
