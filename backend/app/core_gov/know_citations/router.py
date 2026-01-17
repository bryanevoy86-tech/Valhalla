from __future__ import annotations
from fastapi import APIRouter
from . import store

router = APIRouter(prefix="/core/know/citations", tags=["core-know-citations"])

@router.get("")
def get():
    return store.get()

@router.post("")
def link(chunk_id: str, source_id: str):
    return store.link(chunk_id=chunk_id, source_id=source_id)
