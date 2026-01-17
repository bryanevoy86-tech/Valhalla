"""Pantry router (Pack 57)"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.pantry import service as svc
from app.pantry.schemas import *

router = APIRouter(prefix="/pantry", tags=["pantry"])

@router.post("/location", response_model=LocationOut)
def create_location(body: LocationIn, db: Session = Depends(get_db)):
    loc, err = svc.location_create(db, body.name, body.notes)
    if err:
        raise HTTPException(400, err)
    return loc

@router.post("/item", response_model=ItemOut)
def create_item(body: ItemIn, db: Session = Depends(get_db)):
    it = svc.item_create(db, **body.model_dump())
    return it

@router.post("/stock/increment")
def stock_increment(body: StockIn, db: Session = Depends(get_db)):
    st = svc.stock_add(db, body.item_id, body.location_id, body.qty, body.note)
    return {"ok": True, "qty": st.qty}

@router.post("/stock/decrement")
def stock_decrement(body: ConsumeIn, db: Session = Depends(get_db)):
    ok, err = svc.stock_consume(db, body.item_id, body.location_id, body.qty, body.note)
    if not ok:
        raise HTTPException(400, err)
    return {"ok": True}

@router.post("/stock/move")
def stock_move(body: MoveStockIn, db: Session = Depends(get_db)):
    ok, err = svc.stock_move(db, body.item_id, body.from_location_id, body.to_location_id, body.qty, body.note)
    if not ok:
        raise HTTPException(400, err)
    return {"ok": True}

@router.post("/photo")
def add_photo(body: PhotoIn, db: Session = Depends(get_db)):
    ph = svc.photo_add(db, body.item_id, body.file_name, body.alt_text)
    return {"id": ph.id, "detected_tags": ph.detected_tags}

@router.get("/reorders/check")
def reorders_check(db: Session = Depends(get_db)):
    rows = svc.check_reorders(db)
    return [{"item_id": r.item_id, "suggested_qty": r.suggested_qty, "status": r.status} for r in rows]

@router.get("/digest")
def digest(db: Session = Depends(get_db)):
    return svc.weekly_digest(db)
