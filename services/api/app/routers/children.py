"""
Pack 54: Children's Hubs + Vault Guardians - API router
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.children.schemas import *
from app.children import service as svc
from app.children.models import KidsHubChildProfile, Chore

router = APIRouter(prefix="/kids", tags=["kids"])

@router.post("/child", response_model=ChildOut)
def create_child(body: ChildIn, db: Session = Depends(get_db)):
    r = svc.child_create(db, body.model_dump())
    return ChildOut.model_validate(r)

@router.get("/child/{child_id}/wallet", response_model=WalletOut)
def get_wallet(child_id: int, db: Session = Depends(get_db)):
    return svc.wallet_out(db, child_id)

@router.post("/chore", status_code=201)
def add_chore(body: ChoreIn, db: Session = Depends(get_db)):
    r = svc.chore_create(db, body.model_dump())
    return {"id": r.id}

@router.post("/chore/done")
def complete_chore(body: ChoreDone, db: Session = Depends(get_db)):
    r = svc.chore_done(db, body.chore_id)
    if not r:
        raise HTTPException(404, "chore missing/inactive")
    return r

@router.post("/earn", status_code=201)
def earn(body: EarnManual, db: Session = Depends(get_db)):
    svc.earn_manual(db, body.child_id, body.coins, body.memo)
    return {"ok": True}

@router.post("/spend")
def spend(body: SpendReq, db: Session = Depends(get_db)):
    ok, err = svc.spend(db, body.child_id, body.coins, body.memo)
    if not ok:
        raise HTTPException(400, err or "insufficient")
    return {"ok": True}

@router.post("/rules")
def set_rules(body: SaveRuleIn, db: Session = Depends(get_db)):
    r = svc.set_rules(db, body.child_id, body.save_pct, body.invest_pct)
    if not r:
        raise HTTPException(404, "child not found")
    return {"ok": True}

@router.post("/wishlist", status_code=201)
def wishlist(body: WishIn, db: Session = Depends(get_db)):
    r = svc.wishlist_add(db, body.model_dump())
    return {"id": r.id}

@router.post("/idea", status_code=201)
def idea(body: IdeaIn, db: Session = Depends(get_db)):
    r = svc.idea_add(db, body.model_dump())
    return {"id": r.id}

@router.get("/digest/{child_id}", response_model=DigestOut)
def digest(child_id: int, db: Session = Depends(get_db)):
    return svc.weekly_digest(db, child_id)
