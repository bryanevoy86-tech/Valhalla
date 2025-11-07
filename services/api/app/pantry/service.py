"""
Pack 57: Pantry Photo Inventory - Service
"""
import os
from sqlalchemy.orm import Session
from typing import List
from app.pantry.models import PantryLocation, PantryItem, PantryStock, PantryPhoto, PantryTxn, PantryReorder

DEFAULT_LOCATIONS = [l.strip() for l in os.getenv("PANTRY_DEFAULT_LOCATIONS", "Main Pantry,Deep Freezer,Garage Stock").split(",") if l.strip()]

def ensure_default_locations(db: Session):
    for name in DEFAULT_LOCATIONS:
        if not db.query(PantryLocation).filter_by(name=name).first():
            db.add(PantryLocation(name=name))
    db.commit()

def location_create(db: Session, name: str, notes: str | None):
    ensure_default_locations(db)
    if db.query(PantryLocation).filter_by(name=name).first():
        return None, "exists"
    loc = PantryLocation(name=name, notes=notes)
    db.add(loc); db.commit(); db.refresh(loc)
    return loc, None

def item_create(db: Session, **data):
    ensure_default_locations(db)
    it = PantryItem(**data)
    db.add(it); db.commit(); db.refresh(it)
    return it

def stock_add(db: Session, item_id: int, location_id: int, qty: float, note: str | None):
    st = db.query(PantryStock).filter_by(item_id=item_id, location_id=location_id).first()
    if not st:
        st = PantryStock(item_id=item_id, location_id=location_id, qty=0)
        db.add(st)
    st.qty += qty
    db.add(PantryTxn(item_id=item_id, location_id=location_id, kind="in", qty=qty, note=note))
    db.commit(); db.refresh(st)
    return st

def stock_consume(db: Session, item_id: int, location_id: int, qty: float, note: str | None):
    st = db.query(PantryStock).filter_by(item_id=item_id, location_id=location_id).first()
    if not st or st.qty < qty:
        return False, "insufficient"
    st.qty -= qty
    db.add(PantryTxn(item_id=item_id, location_id=location_id, kind="out", qty=qty, note=note))
    db.commit(); db.refresh(st)
    return True, None

def stock_move(db: Session, item_id: int, from_loc: int, to_loc: int, qty: float, note: str | None):
    ok, err = stock_consume(db, item_id, from_loc, qty, note or "move-out")
    if not ok:
        return False, err
    stock_add(db, item_id, to_loc, qty, note or "move-in")
    db.add(PantryTxn(item_id=item_id, location_id=to_loc, kind="move", qty=qty, note=note))
    db.commit()
    return True, None

def photo_add(db: Session, item_id: int | None, file_name: str, alt_text: str | None):
    # naive tag extraction: split filename sans extension on _ and -
    base = os.path.splitext(os.path.basename(file_name))[0]
    parts = [p for p in base.replace("-","_").split("_") if p]
    tags = ",".join(parts[:8]) if parts else None
    ph = PantryPhoto(item_id=item_id, file_name=file_name, alt_text=alt_text, detected_tags=tags)
    db.add(ph); db.commit(); db.refresh(ph)
    # optional: update item tags union
    if item_id:
        it = db.query(PantryItem).filter_by(id=item_id).first()
        if it:
            merged = set((it.tags or '').split(",")) | set(parts)
            it.tags = ",".join(sorted([m for m in merged if m]))
            db.add(it); db.commit()
    return ph

def _total_qty(db: Session, item_id: int) -> float:
    return sum(st.qty for st in db.query(PantryStock).filter_by(item_id=item_id).all())

def check_reorders(db: Session) -> List[PantryReorder]:
    rows = []
    auto_enabled = os.getenv("PANTRY_AUTOREORDER_ENABLED","true").lower()=="true"
    for it in db.query(PantryItem).all():
        total = _total_qty(db, it.id)
        if total < it.reorder_at:
            existing = db.query(PantryReorder).filter_by(item_id=it.id, status="suggested").first()
            if existing:
                rows.append(existing)
                continue
            qty = max(it.target_qty - total, it.reorder_at - total)
            status = "auto" if (auto_enabled and it.auto_reorder) else "suggested"
            r = PantryReorder(item_id=it.id, suggested_qty=qty, status=status)
            db.add(r); db.commit(); db.refresh(r)
            rows.append(r)
    return rows

def weekly_digest(db: Session):
    # simplistic digest: list items below threshold & reorders
    low_stock = []
    for it in db.query(PantryItem).all():
        total = _total_qty(db, it.id)
        if total < it.reorder_at:
            low_stock.append({"item_id": it.id, "name": it.name, "qty": total, "reorder_at": it.reorder_at})
    reorders = check_reorders(db)
    return {
        "low_stock": low_stock,
        "reorders": [
            {"item_id": r.item_id, "suggested_qty": r.suggested_qty, "status": r.status} for r in reorders
        ],
        "total_items": db.query(PantryItem).count(),
    }
