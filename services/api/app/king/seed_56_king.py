"""
Seed for Pack 56: King's Hub
"""
import os, json
from sqlalchemy.orm import Session
from app.king.models import KingProfile, KingVault, KingRule

VAULTS = ["Reserves","Reinvest","Bahamas","Fun"]

def run(db: Session):
    p = db.query(KingProfile).first()
    if not p:
        p = KingProfile(name="All-Seeing Father", currency=os.getenv("KING_BASE_CURRENCY","CAD"))
        db.add(p)
    # ensure vaults
    for lbl in VAULTS:
        if not db.query(KingVault).filter(KingVault.label==lbl).first():
            db.add(KingVault(label=lbl, balance=0, currency=os.getenv("KING_BASE_CURRENCY","CAD")))
    # ensure rules
    if not db.query(KingRule).filter(KingRule.active==True).first():
        default_js = os.getenv("KING_DEFAULT_RULES_JSON","{\"reinvest_pct\":0.90,\"fun_pct\":0.10,\"bahamas_pct\":0.00,\"reserves_pct\":0.00}")
        db.add(KingRule(active=True, rules_json=default_js))
    db.commit()
    print("✅ Seed 56: King ready")
