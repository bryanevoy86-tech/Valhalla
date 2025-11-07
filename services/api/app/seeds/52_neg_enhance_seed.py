"""
Pack 52: Negotiation & Psychology AI Enhancer - Seed defaults
"""
from sqlalchemy.orm import Session
from app.neg_enhance.models import ObjectionRow, RebuttalSnippet, PersonaKnob, EscalationRule


def run(db: Session):
    # Objections
    defaults = [
        ("PRICE", r"(too\s+low|too\s+much|price|numbers\s+don't\s+work)", "med"),
        ("TIMING", r"(later|not\s+ready|tomorrow|next\s+week|think\s+about)", "low"),
        ("TRUST", r"(scam|trust|reviews|who\s+are\s+you)", "high"),
        ("PARTNER", r"(spouse|wife|husband|partner|approval)", "med"),
        ("REPAIRS", r"(repairs|roof|foundation|too\s+much\s+work)", "med"),
    ]
    for c, rx, sev in defaults:
        if not db.query(ObjectionRow).filter_by(code=c).first():
            db.add(ObjectionRow(code=c, pattern_regex=rx, severity=sev))

    # Rebuttals
    snips = [
        ("PRICE", "consultant", "calm", "I hear you on price. If we cover closing costs and take it as-is, what range would feel fair so we can move today?"),
        ("TIMING", "consultant", "empathetic", "Totally fine to think it through. What info would help you feel comfortable deciding sooner?"),
        ("TRUST", "consultant", "analytical", "Happy to verify. I can share references and use an escrow—what proof would you like first?"),
        ("PARTNER", "consultant", "empathetic", "Let’s loop them in. Should we schedule a quick 3-way call so everyone’s on the same page?"),
        ("REPAIRS", "consultant", "calm", "We’ll handle repairs. If we factor that in, does the convenience offset the hassle for you?"),
    ]
    for oc, per, tone, content in snips:
        if not db.query(RebuttalSnippet).filter_by(objection_code=oc, persona=per, tone=tone).first():
            db.add(RebuttalSnippet(objection_code=oc, persona=per, tone=tone, content=content))

    # Persona knobs
    for persona, ask, mirr, depth in [
        ("consultant", 0.15, 0.30, 2),
        ("closer", 0.20, 0.20, 1),
        ("therapist", 0.10, 0.45, 3),
        ("analyst", 0.12, 0.25, 2),
    ]:
        if not db.query(PersonaKnob).filter_by(persona=persona).first():
            db.add(PersonaKnob(persona=persona, ask_softener_pct=ask, mirror_ack_rate=mirr, probe_depth=depth))

    # One escalation rule
    if not db.query(EscalationRule).first():
        db.add(EscalationRule(name="Supervisor Notify", threshold=0.80, action="supervisor_notify", payload_json='{"channel":"ops"}'))

    db.commit()
    print("✅ Pack 52: Negotiation Enhancer seed loaded")
