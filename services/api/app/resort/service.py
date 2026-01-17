"""Pack 58: Resort - Service"""
import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.resort.models import ResortProject, ResortVaultTxn, ResortMilestone, ResortQuote, ResortFunding, ResidencyTimeline, ResidencyStep

def create_project(db: Session, body: dict):
    row = ResortProject(**body); db.add(row); db.commit(); db.refresh(row); return row

def project_status(db: Session, pid: int):
    p = db.query(ResortProject).get(pid)
    if not p: return None
    m = db.query(func.avg(ResortMilestone.percent)).filter(ResortMilestone.project_id==pid).scalar() or 0
    return {
        "id": p.id,
        "name": p.name,
        "currency": p.currency,
        "vault_balance": float(p.vault_balance),
        "target_budget": float(p.target_budget),
        "status": p.status,
        "milestone_avg": float(m)
    }

def vault_inflow(db: Session, pid: int, amount: float, note: str | None):
    p = db.query(ResortProject).get(pid)
    if not p: return None
    amt = Decimal(str(amount))
    p.vault_balance = Decimal(p.vault_balance) + amt
    db.add(ResortVaultTxn(project_id=pid, kind="inflow", amount=amt, note=note))
    db.commit(); db.refresh(p)
    return float(p.vault_balance)

def vault_outflow(db: Session, pid: int, amount: float, note: str | None):
    p = db.query(ResortProject).get(pid)
    if not p: return None, "missing project"
    amt = Decimal(str(amount))
    if Decimal(p.vault_balance) < amt: return None, "insufficient"
    p.vault_balance = Decimal(p.vault_balance) - amt
    db.add(ResortVaultTxn(project_id=pid, kind="outflow", amount=amt, note=note))
    db.commit(); db.refresh(p)
    return float(p.vault_balance), None

def milestone_add(db: Session, body: dict):
    row = ResortMilestone(**body); db.add(row); db.commit(); db.refresh(row); return row

def milestone_update(db: Session, mid: int, status: str, percent: float | None):
    m = db.query(ResortMilestone).get(mid)
    if not m: return None
    m.status = status
    if percent is not None: m.percent = percent
    db.commit(); db.refresh(m); return m

def quote_add(db: Session, body: dict):
    row = ResortQuote(**body); db.add(row); db.commit(); db.refresh(row); return row

def quote_set_status(db: Session, qid: int, status: str):
    q = db.query(ResortQuote).get(qid)
    if not q: return None
    q.status = status
    db.commit(); db.refresh(q); return q

def funding_add(db: Session, body: dict):
    row = ResortFunding(**body); db.add(row); db.commit(); db.refresh(row); return row

def residency_create(db: Session, body: dict):
    row = ResidencyTimeline(**body); db.add(row); db.commit(); db.refresh(row); return row

def residency_step_add(db: Session, body: dict):
    row = ResidencyStep(**body); db.add(row); db.commit(); db.refresh(row); return row

def residency_progress(db: Session, tid: int):
    t = db.query(ResidencyTimeline).get(tid)
    if not t: return None
    pct = db.query(func.avg(ResidencyStep.percent)).filter(ResidencyStep.timeline_id==tid).scalar() or 0
    return {
        "country": t.country,
        "status": t.status,
        "target_date": str(t.target_date) if t.target_date else None,
        "percent": float(pct),
        "min_capital": float(t.min_capital)
    }

def weekly_digest(db: Session):
    lines = []
    for p in db.query(ResortProject).all():
        tb = float(p.target_budget)
        if tb > 0:
            pct = round((float(p.vault_balance)/tb)*100, 2) if tb else 0
            lines.append(f"{p.name}: vault {p.vault_balance}/{p.target_budget} ({pct}%)")
    # milestones due within 14 days
    today = datetime.date.today()
    cutoff = today + datetime.timedelta(days=14)
    ms = db.query(ResortMilestone).filter(ResortMilestone.due_date != None, ResortMilestone.due_date <= cutoff, ResortMilestone.status != "done").all()
    for m in ms:
        lines.append(f"Milestone due: {m.name} ({m.code}) by {m.due_date}")
    return {"lines": lines or ["Quiet week — no urgent resort actions."]}
