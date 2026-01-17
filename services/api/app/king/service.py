"""
Pack 56: King's Hub + Adaptive Vault Scaling - Service layer
"""
import os, json, datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from app.king.models import KingProfile, KingVault, KingRule, KingTxn, BahamasProgress

VAULTS = ["Reserves","Reinvest","Bahamas","Fun"]

def _profile(db: Session) -> KingProfile:
    p = db.query(KingProfile).first()
    if p:
        return p
    p = KingProfile(name="All-Seeing Father", currency=os.getenv("KING_BASE_CURRENCY","CAD"))
    db.add(p); db.commit(); db.refresh(p)
    return p

def _vault(db: Session, label: str) -> KingVault:
    v = db.query(KingVault).filter(KingVault.label==label).first()
    if v:
        return v
    v = KingVault(label=label, balance=0, currency=os.getenv("KING_BASE_CURRENCY","CAD"))
    db.add(v); db.commit(); db.refresh(v)
    return v

def _rules(db: Session) -> dict:
    r = db.query(KingRule).filter(KingRule.active==True).order_by(KingRule.id.desc()).first()
    if r:
        return json.loads(r.rules_json)
    default_js = os.getenv("KING_DEFAULT_RULES_JSON",'{"reinvest_pct":0.90,"fun_pct":0.10,"bahamas_pct":0.00,"reserves_pct":0.00}')
    r = KingRule(active=True, rules_json=default_js)
    db.add(r); db.commit()
    return json.loads(default_js)

def _bahamas(db: Session) -> BahamasProgress:
    b = db.query(BahamasProgress).first()
    if b:
        return b
    b = BahamasProgress(
        target_amount=Decimal(str(os.getenv("KING_BAHAMAS_TARGET","500000"))),
        monthly_min=Decimal(str(os.getenv("KING_BAHAMAS_MIN_MONTHLY","5000")))
    )
    db.add(b); db.commit(); db.refresh(b)
    return b

def _ensure_vaults(db: Session):
    for lbl in VAULTS:
        _vault(db, lbl)

def status(db: Session):
    _profile(db); _ensure_vaults(db)
    rules = _rules(db)
    b = _bahamas(db)
    vs = {lbl: float(_vault(db, lbl).balance) for lbl in VAULTS}
    progress = {
        "target": float(b.target_amount),
        "bahamas": vs["Bahamas"],
        "pct_to_target": round((vs["Bahamas"]/float(b.target_amount))*100.0 if float(b.target_amount) else 0.0, 2)
    }
    return {"currency": os.getenv("KING_BASE_CURRENCY","CAD"), "vaults": vs, "rules": rules, "bahamas_progress": progress}

def set_rules(db: Session, rule_in: dict):
    # normalize to sum=1.0
    total = sum(rule_in.values())
    if total <= 0:
        raise ValueError("Rules sum must be > 0")
    norm = {k: round(v/total,4) for k,v in rule_in.items()}
    # deactivate previous
    db.query(KingRule).filter(KingRule.active==True).update({"active": False})
    row = KingRule(active=True, rules_json=json.dumps(norm))
    db.add(row); db.commit()
    return norm

def _alloc(db: Session, gross: Decimal, rules: dict):
    parts = {
        "Reinvest": gross*Decimal(str(rules.get("reinvest_pct",0))),
        "Fun": gross*Decimal(str(rules.get("fun_pct",0))),
        "Bahamas": gross*Decimal(str(rules.get("bahamas_pct",0))),
        "Reserves": gross*Decimal(str(rules.get("reserves_pct",0))),
    }
    return parts

def _txn(db: Session, lbl: str, amount: Decimal, note: str, kind: str):
    v = _vault(db, lbl)
    v.balance = Decimal(v.balance) + amount
    db.add(KingTxn(vault_id=v.id, kind=kind, amount=amount, note=note))

def inflow(db: Session, amount: float, note: str | None):
    _ensure_vaults(db)
    rules = _rules(db)
    gross = Decimal(str(amount))
    # Adaptive nudges: if Reserves below target, siphon a step from Reinvest -> Reserves
    step = Decimal(str(os.getenv("KING_RULE_ADJUST_STEP","0.05")))
    min_res = Decimal(str(os.getenv("KING_MIN_RESERVES_TARGET","25000")))
    res_bal = Decimal(str(_vault(db,"Reserves").balance or 0))
    if os.getenv("KING_ADAPTIVE_ENABLED","true").lower()=="true" and res_bal < min_res and Decimal(str(rules.get("reinvest_pct",0))) >= step:
        rules["reinvest_pct"] = round(float(Decimal(str(rules["reinvest_pct"])) - step), 4)
        rules["reserves_pct"] = round(float(Decimal(str(rules.get("reserves_pct",0))) + step), 4)
        set_rules(db, rules)

    parts = _alloc(db, gross, _rules(db))
    for lbl, amt in parts.items():
        if amt and amt != 0:
            _txn(db, lbl, amt, note or "inflow allocation", "inflow")
    db.commit()
    return {k: float(v) for k,v in parts.items()}

def spend(db: Session, vault: str, amount: float, note: str | None):
    v = _vault(db, vault)
    amt = Decimal(str(amount))
    if Decimal(v.balance) < amt:
        return False, "Insufficient balance"
    v.balance = Decimal(v.balance) - amt
    db.add(KingTxn(vault_id=v.id, kind="outflow", amount=amt, note=note))
    db.commit()
    return True, None
