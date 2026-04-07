"""
Pack 57: Pantry Photo Inventory - Schemas
"""
from pydantic import BaseModel
from typing import Optional, List, Dict

class LocationIn(BaseModel):
    name: str
    notes: Optional[str] = None

class ItemIn(BaseModel):
    name: str
    tags: Optional[str] = None
    unit: Optional[str] = "ea"
    reorder_at: Optional[float] = 1.0
    target_qty: Optional[float] = 2.0
    auto_reorder: Optional[bool] = True

class StockIn(BaseModel):
    item_id: int
    location_id: int
    qty: float
    note: Optional[str] = None

class MoveStockIn(BaseModel):
    item_id: int
    from_location_id: int
    to_location_id: int
    qty: float
    note: Optional[str] = None

class ConsumeIn(BaseModel):
    item_id: int
    location_id: int
    qty: float
    note: Optional[str] = None

class PhotoIn(BaseModel):
    item_id: Optional[int] = None
    file_name: str
    alt_text: Optional[str] = None

class ReorderSuggest(BaseModel):
    item_id: int
    suggested_qty: float
    status: str

class DigestOut(BaseModel):
    low_stock: List[Dict[str, float]]
    reorders: List[ReorderSuggest]
    total_items: int

class LocationOut(BaseModel):
    id: int
    name: str
    notes: Optional[str]
    class Config:
        from_attributes = True

class ItemOut(BaseModel):
    id: int
    name: str
    tags: Optional[str]
    unit: str
    reorder_at: float
    target_qty: float
    auto_reorder: bool
    class Config:
        from_attributes = True
