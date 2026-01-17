"""
Grants router - manages grant sources and records, generates grant packs with scoring.
"""

from typing import List, Optional
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ..core.db import get_db
from ..core.dependencies import require_builder_key
from ..models.grants import GrantSource, GrantRecord
from ..schemas.grants import (
    GrantSourceIn, GrantSourceOut, GrantIn, GrantOut, 
    GrantCriteria, GrantPack, GrantHit
)

router = APIRouter(prefix="/grants", tags=["grants"])


# ---------- Sources ----------
@router.post("/sources", response_model=GrantSourceOut)
def add_source(
    payload: GrantSourceIn, 
    db: Session = Depends(get_db), 
    _: bool = Depends(require_builder_key)
):
    """Add a new grant source."""
    s = GrantSource(
        name=payload.name, 
        url=payload.url, 
        region=payload.region, 
        tags=payload.tags, 
        active=payload.active
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


@router.get("/sources", response_model=List[GrantSourceOut])
def list_sources(
    only_active: bool = Query(False), 
    db: Session = Depends(get_db), 
    _: bool = Depends(require_builder_key)
):
    """List all grant sources."""
    q = db.query(GrantSource)
    if only_active:
        q = q.filter(GrantSource.active.is_(True))
    return q.order_by(GrantSource.id.desc()).all()


# ---------- Records ----------
@router.post("", response_model=GrantOut)
def add_grant(
    payload: GrantIn, 
    db: Session = Depends(get_db), 
    _: bool = Depends(require_builder_key)
):
    """Add a new grant record."""
    row = GrantRecord(**payload.dict())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("", response_model=List[GrantOut])
def list_grants(
    db: Session = Depends(get_db), 
    _: bool = Depends(require_builder_key)
):
    """List recent grant records (limit 500)."""
    return db.query(GrantRecord).order_by(GrantRecord.id.desc()).limit(500).all()


# ---------- Generator (scoring + JSON) ----------
def _score(record: GrantRecord, crit: GrantCriteria) -> tuple[float, str]:
    """Score a grant record against criteria."""
    score = 0.0
    reasons = []
    
    if crit.region and record.region and crit.region.lower() in record.region.lower():
        score += 0.4
        reasons.append("region match")
    
    if crit.categories and record.category and record.category in crit.categories:
        score += 0.3
        reasons.append("category match")
    
    if crit.min_amount and record.amount_max:
        if float(record.amount_max) >= crit.min_amount:
            score += 0.2
            reasons.append("amount ≥ min")
    
    if crit.max_deadline and record.deadline:
        if record.deadline <= crit.max_deadline:
            score += 0.1
            reasons.append("deadline within window")
    
    return score, ", ".join(reasons) or "baseline"


@router.post("/generate", response_model=GrantPack)
def generate_pack(
    crit: GrantCriteria, 
    db: Session = Depends(get_db), 
    _: bool = Depends(require_builder_key)
):
    """Generate a scored grant pack based on criteria."""
    rows = db.query(GrantRecord).all()
    hits: List[GrantHit] = []
    
    for r in rows:
        s, why = _score(r, crit)
        amount_est = float(r.amount_max or r.amount_min or 0)
        hits.append(GrantHit(
            id=r.id, 
            title=r.title, 
            program=r.program, 
            region=r.region, 
            category=r.category,
            amount_estimate=amount_est if amount_est > 0 else None,
            deadline=r.deadline, 
            link=r.link, 
            score=round(s, 4), 
            reason=why
        ))
    
    hits.sort(key=lambda h: h.score, reverse=True)
    hits = hits[:max(1, min(crit.limit, 100))]
    
    return GrantPack(total=len(hits), hits=hits)


# ---------- Export PDF (lightweight) ----------
@router.post("/export/pdf")
def export_pdf(
    crit: GrantCriteria, 
    db: Session = Depends(get_db), 
    _: bool = Depends(require_builder_key)
):
    """Export grant pack as PDF."""
    pack = generate_pack(crit, db)  # reuse logic
    
    # Build PDF
    from reportlab.lib.pagesizes import LETTER
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import inch
    import os
    import tempfile
    
    # Use tempfile for cross-platform compatibility
    fd, out_path = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)
    
    c = canvas.Canvas(out_path, pagesize=LETTER)
    width, height = LETTER
    x, y = 0.7 * inch, height - 0.8 * inch
    
    c.setFont("Helvetica-Bold", 14)
    c.drawString(x, y, "Valhalla — Grant Pack")
    y -= 0.3 * inch
    
    c.setFont("Helvetica", 10)
    c.drawString(x, y, f"Region: {crit.region or 'any'}  Categories: {', '.join(crit.categories or []) or 'any'}")
    y -= 0.25 * inch
    c.drawString(x, y, f"Limit: {crit.limit}")
    y -= 0.25 * inch
    
    for i, h in enumerate(pack.hits, 1):
        if y < 1.0 * inch:
            c.showPage()
            y = height - 0.8 * inch
            c.setFont("Helvetica-Bold", 12)
        
        c.setFont("Helvetica-Bold", 12)
        c.drawString(x, y, f"{i}. {h.title}  (score {h.score:.2f})")
        y -= 0.2 * inch
        
        c.setFont("Helvetica", 9)
        line = f"{(h.program or '')} • {h.region or '—'} • {h.category or '—'} • up to {h.amount_estimate or '—'} • deadline {h.deadline or '—'}"
        c.drawString(x, y, line[:110])
        y -= 0.18 * inch
        
        if h.link:
            c.setFillColorRGB(0, 0, 1)
            c.drawString(x, y, (h.link or "")[:110])
            c.setFillColorRGB(0, 0, 0)
            y -= 0.18 * inch
        
        c.drawString(x, y, f"Why: {h.reason}")
        y -= 0.28 * inch
    
    c.showPage()
    c.save()
    
    return FileResponse(out_path, media_type="application/pdf", filename="grant_pack.pdf")
