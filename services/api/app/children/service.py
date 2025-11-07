"""
Pack 54: Children's Hubs + Vault Guardians - Service layer
"""
import os
import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.children.models import (
    ChildProfile, VaultGuardian, Chore, ChoreLog, CoinWallet, CoinTxn, WishlistItem, IdeaSubmission
)

def _rate():
    return float(os.getenv("KIDS_COIN_EXCHANGE_RATE", "0.01"))

def _wallet(db: Session, child_id: int) -> CoinWallet:
    w = db.query(CoinWallet).filter(CoinWallet.child_id == child_id).first()
    if not w:
        w = CoinWallet(child_id=child_id, spendable=0, savings=0, invested=0)
        db.add(w)
        db.commit()
        db.refresh(w)
    return w

def child_create(db: Session, body: dict):
    row = ChildProfile(**body)
    db.add(row)
    db.commit()
    db.refresh(row)
    # default guardian
    if not db.query(VaultGuardian).filter(VaultGuardian.child_id == row.id).first():
        db.add(VaultGuardian(child_id=row.id, name="Vault Dragon", personality="gentle", lore="Guardian of your gold."))
        db.commit()
    _wallet(db, row.id)
    return row

def chore_create(db: Session, body: dict):
    row = Chore(**body)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row

def chore_done(db: Session, chore_id: int):
    c = db.query(Chore).get(chore_id)
    if not c or not c.active:
        return None
    log = ChoreLog(chore_id=chore_id, coins_awarded=c.coins)
    db.add(log)
    # split per save/invest rules
    kid = db.query(ChildProfile).get(c.child_id)
    w = _wallet(db, c.child_id)
    save_pct = kid.save_pct
    invest_pct = kid.invest_pct
    save_amt = int(round(c.coins * save_pct))
    invest_amt = int(round(c.coins * invest_pct))
    spend_amt = c.coins - save_amt - invest_amt
    w.savings += save_amt
    w.invested += invest_amt
    w.spendable += spend_amt
    db.add(CoinTxn(child_id=c.child_id, kind="earn", amount=c.coins, memo=f"Chore: {c.title}"))
    if save_amt:
        db.add(CoinTxn(child_id=c.child_id, kind="save", amount=save_amt, memo="Auto-save"))
    if invest_amt:
        db.add(CoinTxn(child_id=c.child_id, kind="invest", amount=invest_amt, memo="Auto-invest"))
    db.commit()
    db.refresh(w)
    return dict(awarded=c.coins, split={"spend": spend_amt, "save": save_amt, "invest": invest_amt})

def earn_manual(db: Session, child_id: int, coins: int, memo: str | None):
    w = _wallet(db, child_id)
    kid = db.query(ChildProfile).get(child_id)
    save_amt = int(round(coins * kid.save_pct))
    invest_amt = int(round(coins * kid.invest_pct))
    spend_amt = coins - save_amt - invest_amt
    w.spendable += spend_amt
    w.savings += save_amt
    w.invested += invest_amt
    db.add(CoinTxn(child_id=child_id, kind="earn", amount=coins, memo=memo or "manual"))
    if save_amt:
        db.add(CoinTxn(child_id=child_id, kind="save", amount=save_amt, memo="Auto-save"))
    if invest_amt:
        db.add(CoinTxn(child_id=child_id, kind="invest", amount=invest_amt, memo="Auto-invest"))
    db.commit()
    db.refresh(w)
    return True

def spend(db: Session, child_id: int, coins: int, memo: str | None):
    w = _wallet(db, child_id)
    if w.spendable < coins:
        return False, "Insufficient spendable"
    w.spendable -= coins
    db.add(CoinTxn(child_id=child_id, kind="spend", amount=coins, memo=memo or "spend"))
    db.commit()
    return True, None

def set_rules(db: Session, child_id: int, save_pct: float, invest_pct: float):
    kid = db.query(ChildProfile).get(child_id)
    if not kid:
        return None
    kid.save_pct = save_pct
    kid.invest_pct = invest_pct
    db.commit()
    db.refresh(kid)
    return kid

def wallet_out(db: Session, child_id: int):
    w = _wallet(db, child_id)
    return {
        "spendable": w.spendable,
        "savings": w.savings,
        "invested": w.invested,
        "fiat_equiv": round(_rate() * (w.spendable + w.savings + w.invested), 2)
    }

def wishlist_add(db: Session, body: dict):
    row = WishlistItem(**body)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row

def idea_add(db: Session, body: dict):
    row = IdeaSubmission(**body)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row

def accrue_interest(db: Session, child_id: int, days: int = 7):
    # simple APR prorated daily on invested
    w = _wallet(db, child_id)
    apr = float(os.getenv("KIDS_INVEST_APR", "0.05"))
    daily = apr / 365.0
    interest = int(round(w.invested * daily * days))
    if interest > 0:
        w.invested += interest
        db.add(CoinTxn(child_id=child_id, kind="interest", amount=interest, memo=f"{days}d interest"))
        db.commit()
    return interest

def weekly_digest(db: Session, child_id: int):
    # summarize last 7 days txns
    since = func.datetime(func.current_timestamp(), "-7 day")
    txns = db.query(CoinTxn).filter(CoinTxn.child_id == child_id, CoinTxn.created_at >= since).all()
    lines = [f"{t.kind}+{t.amount} ({t.memo or ''})" for t in txns]
    return {"lines": lines or ["No activity this week."]}
