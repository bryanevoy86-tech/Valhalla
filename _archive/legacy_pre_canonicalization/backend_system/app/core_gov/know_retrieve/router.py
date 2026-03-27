from __future__ import annotations
from fastapi import APIRouter
from .service import search

router = APIRouter(prefix="/core/know/retrieve", tags=["core-know-retrieve"])

@router.get("")
def get(query: str, limit: int = 8):
    return search(query=query, limit=limit)
