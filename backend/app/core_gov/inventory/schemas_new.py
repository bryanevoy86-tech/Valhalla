from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

Status = Literal["active", "archived"]

class LocationCreate(BaseModel):
    name: str
    status: Status = "active"
    notes: str = ""
    meta: Dict[str, Any] = Field(default_factory=dict)

class ItemCreate(BaseModel):
    name: str
    location_id: str
    status: Status = "active"
    qty: float = 0.0
    unit: str = "each"         # each, rolls, L, kg, etc.
    reorder_point: float = 0.0 # trigger
    desired_qty: float = 0.0   # target stock
    category: str = "general"  # groceries, toiletries, clothing, home
    tags: List[str] = Field(default_factory=list)
    notes: str = ""
    meta: Dict[str, Any] = Field(default_factory=dict)

class InventoryExport(BaseModel):
    locations: List[Dict[str, Any]]
    items: List[Dict[str, Any]]
