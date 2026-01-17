"""Seed Pack 58: Resort default project + residency"""
import os, datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from app.resort.models import ResortProject, ResortMilestone, ResidencyTimeline, ResidencyStep

def run(db: Session):
    name = os.getenv("RESORT_DEFAULT_NAME","Bahamas Phase 1")
    proj = db.query(ResortProject).filter_by(name=name).first()
    if not proj:
        proj = ResortProject(
            name=name,
            currency=os.getenv("RESORT_BASE_CURRENCY","USD"),
            target_budget=Decimal(str(os.getenv("RESORT_TARGET_BUDGET","2500000"))),
            vault_balance=0,
            status="planning"
        )
        db.add(proj); db.commit(); db.refresh(proj)
        seeds = [
            ("LAND_IOI","Land / Turnkey target shortlist"),
            ("DUE_DIL","Legal & financial due diligence"),
            ("PERMITS","Permits & licensing"),
            ("FINANCE","Funding package finalized"),
            ("BUILD_START","Construction start"),
            ("SOFT_OPEN","Soft opening"),
        ]
        for code, namex in seeds:
            db.add(ResortMilestone(project_id=proj.id, code=code, name=namex))
        db.commit()
    rt = db.query(ResidencyTimeline).filter_by(country="Bahamas").first()
    if not rt:
        tdate = os.getenv("RESIDENCY_TARGET_DATE","2027-01-15")
        rt = ResidencyTimeline(
            country="Bahamas",
            target_date=datetime.date.fromisoformat(tdate),
            min_capital=Decimal(str(os.getenv("RESIDENCY_MIN_CAPITAL","750000"))),
            status="planning"
        )
        db.add(rt); db.commit(); db.refresh(rt)
        for code, nm in [
            ("PASSPORT_RENEW","Passport renewal (express)"),
            ("POLICE_CERT","Police certificate"),
            ("LAWYER_ENGAGE","Engage local lawyer"),
            ("APP_SUBMIT","Residency application submitted"),
            ("FEES_PAID","Government fees paid"),
        ]:
            db.add(ResidencyStep(timeline_id=rt.id, code=code, name=nm))
        db.commit()
    print("✅ Seed 58: Resort + Residency ready")
