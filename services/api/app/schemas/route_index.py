"""
PACK TY: Route Index & Debug Explorer Schemas
"""

from typing import List, Optional
from pydantic import BaseModel


class RouteInfo(BaseModel):
    path: str
    methods: List[str]
    name: str
    tags: List[str]
    summary: Optional[str] = None
    deprecated: bool = False


class RouteIndex(BaseModel):
    total: int
    routes: List[RouteInfo]
