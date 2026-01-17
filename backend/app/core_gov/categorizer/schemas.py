from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


RuleType = Literal["vendor_contains", "tag_contains", "notes_contains"]
Status = Literal["active", "paused"]


class CategoryRuleCreate(BaseModel):
    name: str
    status: Status = "active"
    rule_type: RuleType = "vendor_contains"
    pattern: str                   # lowercase match
    category: str                  # "groceries", "utilities", "tools", "marketing", etc.
    confidence: float = 0.7
    tags_add: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)


class CategoryRuleRecord(BaseModel):
    id: str
    name: str
    status: Status
    rule_type: RuleType
    pattern: str
    category: str
    confidence: float
    tags_add: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class RuleListResponse(BaseModel):
    items: List[CategoryRuleRecord]


class CategorizeReceiptRequest(BaseModel):
    receipt_id: str
    apply: bool = True             # if true, patches receipt
    meta: Dict[str, Any] = Field(default_factory=dict)


class CategorizeReceiptResponse(BaseModel):
    receipt_id: str
    category: str = ""
    confidence: float = 0.0
    matched_rule_id: str = ""
    matched_rule_name: str = ""
    tags_add: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    receipt_snapshot: Dict[str, Any] = Field(default_factory=dict)
