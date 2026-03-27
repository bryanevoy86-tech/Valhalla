from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


Location = Literal["pantry", "garage", "deep_freezer", "fridge", "bathroom", "shop", "other"]
Unit = Literal["count", "roll", "box", "lb", "kg", "g", "oz", "l", "ml", "pack", "case", "other"]
Priority = Literal["low", "normal", "high", "critical"]


class ItemCreate(BaseModel):
    name: str
    location: Location = "pantry"
    unit: Unit = "count"
    on_hand: float = 0
    min_threshold: float = 0
    reorder_qty: float = 0
    cadence_days: int = 0            # optional: reorder cadence estimate
    priority: Priority = "normal"
    preferred_brand: str = ""
    preferred_store: str = ""
    est_unit_cost: float = 0.0       # optional for budgeting
    tags: List[str] = Field(default_factory=list)
    notes: str = ""
    meta: Dict[str, Any] = Field(default_factory=dict)


class ItemRecord(BaseModel):
    id: str
    name: str
    location: Location
    unit: Unit
    on_hand: float
    min_threshold: float
    reorder_qty: float
    cadence_days: int
    priority: Priority
    preferred_brand: str = ""
    preferred_store: str = ""
    est_unit_cost: float = 0.0
    tags: List[str] = Field(default_factory=list)
    notes: str = ""
    meta: Dict[str, Any] = Field(default_factory=dict)
    last_updated: str = ""
    last_purchased: str = ""
    created_at: datetime
    updated_at: datetime


class ItemListResponse(BaseModel):
    items: List[ItemRecord]


class AdjustRequest(BaseModel):
    delta: float                      # + adds stock, - consumes
    reason: str = ""
    meta: Dict[str, Any] = Field(default_factory=dict)
