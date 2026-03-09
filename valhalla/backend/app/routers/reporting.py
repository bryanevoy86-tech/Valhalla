from typing import Any, Dict

from app.deps.auth import get_current_user
from app.deps.tenant import get_db, org_membership
from app.models.saved_chart import Dashboard, SavedChart
from app.services.reporting import run_metric
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

router = APIRouter(prefix="/reporting", tags=["reporting"])


@router.post("/metric")
def metric(payload: Dict[str, Any], ctx=Depends(org_membership()), db: Session = Depends(get_db)):
    metric = payload.get("metric")
    rng = payload.get("range", "30d")
    try:
        data = run_metric(db, ctx["org_id"], metric, rng)
        return {"metric": metric, "range": rng, "data": data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/charts")
def list_charts(
    ctx=Depends(org_membership()), db: Session = Depends(get_db), user=Depends(get_current_user)
):
    rows = (
        db.query(SavedChart)
        .filter(SavedChart.org_id == ctx["org_id"])
        .filter((SavedChart.user_id == user.id) | (SavedChart.shared == True))
        .order_by(SavedChart.name.asc())
        .all()
    )
    return [
        {"id": r.id, "name": r.name, "viz": r.viz, "spec": r.spec, "shared": r.shared} for r in rows
    ]


@router.post("/charts")
def create_chart(
    payload: Dict[str, Any],
    ctx=Depends(org_membership()),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    c = SavedChart(
        org_id=ctx["org_id"],
        user_id=user.id,
        name=payload["name"],
        viz=payload.get("viz", "line"),
        spec=payload.get("spec", {}),
        shared=bool(payload.get("shared", False)),
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return {"id": c.id}


@router.patch("/charts/{chart_id}")
def update_chart(
    chart_id: int,
    payload: Dict[str, Any],
    ctx=Depends(org_membership()),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    c = (
        db.query(SavedChart)
        .filter(SavedChart.id == chart_id, SavedChart.org_id == ctx["org_id"])
        .first()
    )
    if not c:
        raise HTTPException(status_code=404, detail="Not found")
    if c.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not your chart")
    for k in ["name", "viz", "spec", "shared"]:
        if k in payload:
            setattr(c, k, payload[k])
    db.commit()
    return {"ok": True}


@router.delete("/charts/{chart_id}")
def delete_chart(
    chart_id: int,
    ctx=Depends(org_membership()),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    c = (
        db.query(SavedChart)
        .filter(SavedChart.id == chart_id, SavedChart.org_id == ctx["org_id"])
        .first()
    )
    if not c:
        raise HTTPException(status_code=404, detail="Not found")
    if c.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not your chart")
    db.delete(c)
    db.commit()
    return {"ok": True}


@router.get("/dashboards")
def list_dashboards(
    ctx=Depends(org_membership()), db: Session = Depends(get_db), user=Depends(get_current_user)
):
    rows = (
        db.query(Dashboard)
        .filter(Dashboard.org_id == ctx["org_id"])
        .filter((Dashboard.user_id == user.id) | (Dashboard.shared == True))
        .order_by(Dashboard.name.asc())
        .all()
    )
    return [{"id": r.id, "name": r.name, "layout": r.layout, "shared": r.shared} for r in rows]


@router.post("/dashboards")
def create_dashboard(
    payload: Dict[str, Any],
    ctx=Depends(org_membership()),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    d = Dashboard(
        org_id=ctx["org_id"],
        user_id=user.id,
        name=payload["name"],
        layout=payload.get("layout", []),
        shared=bool(payload.get("shared", False)),
    )
    db.add(d)
    db.commit()
    db.refresh(d)
    return {"id": d.id}


@router.patch("/dashboards/{dash_id}")
def update_dashboard(
    dash_id: int,
    payload: Dict[str, Any],
    ctx=Depends(org_membership()),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    d = (
        db.query(Dashboard)
        .filter(Dashboard.id == dash_id, Dashboard.org_id == ctx["org_id"])
        .first()
    )
    if not d:
        raise HTTPException(status_code=404, detail="Not found")
    if d.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not your dashboard")
    for k in ["name", "layout", "shared"]:
        if k in payload:
            setattr(d, k, payload[k])
    db.commit()
    return {"ok": True}
