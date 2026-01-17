"""Seed for Pack 57 Pantry"""
import os
from sqlalchemy.orm import Session
from app.pantry.models import PantryLocation, PantryItem, PantryStock

DEFAULT_LOCATIONS = [l.strip() for l in os.getenv("PANTRY_DEFAULT_LOCATIONS", "Main Pantry,Deep Freezer,Garage Stock").split(",") if l.strip()]

def run(db: Session):
    # ensure default locations
    locs = []
    for name in DEFAULT_LOCATIONS:
        loc = db.query(PantryLocation).filter_by(name=name).first()
        if not loc:
            loc = PantryLocation(name=name)
            db.add(loc); db.commit(); db.refresh(loc)
        locs.append(loc)
    # staple items
    staples = [
        {"name": "Milk", "unit": "ea", "reorder_at": 1, "target_qty": 2},
        {"name": "Eggs", "unit": "ea", "reorder_at": 1, "target_qty": 2},
    ]
    for s in staples:
        it = db.query(PantryItem).filter_by(name=s["name"]).first()
        if not it:
            it = PantryItem(**s)
            db.add(it); db.commit(); db.refresh(it)
        # initial stock of 1 in first location
        st = db.query(PantryStock).filter_by(item_id=it.id, location_id=locs[0].id).first()
        if not st:
            st = PantryStock(item_id=it.id, location_id=locs[0].id, qty=1)
            db.add(st)
    db.commit()
    print("✅ Seed 57: Pantry ready")
