"""
Pack 53: Black Ice Tier II + Shadow Contingency - Seed defaults
"""
from sqlalchemy.orm import Session
from app.blackice import service as svc

def run(db: Session):
    # Default protocol
    if not db.query(svc.BlackIceProtocol).filter_by(name="Tier II Protocol").first():
        svc.create_protocol(db, name="Tier II Protocol", level=2, description="Default separation protocol for critical events.")
    # Default continuity window
    p = db.query(svc.BlackIceProtocol).filter_by(name="Tier II Protocol").first()
    if p and not db.query(svc.ContinuityWindow).filter_by(protocol_id=p.id).first():
        svc.add_continuity(db, protocol_id=p.id, min_hours=72, alert_channel="ops", notes="Default 72h continuity window.")
    # Default key rotation checklist
    checklist = ["api","oauth","webhooks","ssh","db","cdn","emails","storage"]
    for item in checklist:
        if not db.query(svc.KeyRotationCheck).filter_by(protocol_id=p.id, checklist_item=item).first():
            svc.add_key_check(db, protocol_id=p.id, checklist_item=item)
    db.commit()
    print("✅ Pack 53: Black Ice seed loaded")
