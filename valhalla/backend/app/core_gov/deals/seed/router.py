from __future__ import annotations

from fastapi import APIRouter
from app.core_gov.audit.audit_log import audit
from app.core_gov.deals.store import add_deal
from app.core_gov.deals.seed.generator import generate_seed_batch

router = APIRouter(prefix="/deals/seed", tags=["Core: Deals"])

@router.post("/generate")
def generate(n: int = 200, ca_ratio: float = 0.5):
    batch = generate_seed_batch(n=n, ca_ratio=ca_ratio)
    created = []
    for d in batch:
        created.append(add_deal(d))
    audit("DEALS_SEED_GENERATED", {"count": len(created), "ca_ratio": ca_ratio})
    return {"ok": True, "created": len(created)}
