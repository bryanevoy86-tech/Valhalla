from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
import sqlalchemy as sa
from app.db import get_db

router = APIRouter()

@router.get("/match")
def match_buyers(lead_id: str, db: Session = Depends(get_db)):
    lead = db.execute(sa.text("SELECT id, city, ask FROM leads WHERE id=:id"), {"id": lead_id}).mappings().first()
    if not lead:
        raise HTTPException(404, "lead not found")
    buyers = db.execute(sa.text("SELECT id, name, buy_box FROM buyers WHERE buy_box IS NOT NULL")).mappings().all()
    ranked = []
    for b in buyers:
        box = b["buy_box"] or {}
        score = 0
        mn, mx = box.get("min_price"), box.get("max_price")
        if isinstance(mn, (int,float)) and isinstance(mx, (int,float)):
            if mn <= lead["ask"] <= mx: score += 50
        areas = set((box.get("areas") or []) + (box.get("zip_list") or []))
        if lead["city"] and (not areas or lead["city"] in areas): score += 30
        if box.get("close_days"): score += 20
        ranked.append({"buyer_id": b["id"], "name": b["name"], "score": score})
    ranked.sort(key=lambda x: x["score"], reverse=True)
    return {"lead_id": lead_id, "results": ranked[:10]}
