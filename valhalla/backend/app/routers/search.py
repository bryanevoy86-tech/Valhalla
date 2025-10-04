from typing import Any, Dict

from app.deps.auth import get_current_user
from app.deps.tenant import get_db, org_membership
from app.models.deal import Deal
from app.models.legacy import Legacy
from app.models.saved_view import RecentSearch, SavedView
from app.services.query_builder import apply_filters, apply_sort, paginate
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

router = APIRouter(prefix="/search", tags=["search"])


def _entity_map(entity: str):
    if entity == "legacies":
        return Legacy
    if entity == "deals":
        return Deal
    raise HTTPException(status_code=400, detail=f"Unsupported entity: {entity}")


@router.post("/{entity}")
def search_entity(
    entity: str,
    payload: Dict[str, Any],
    ctx=Depends(org_membership()),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    model = _entity_map(entity)
    filters = payload.get("filters")
    sort = payload.get("sort")
    page = int(payload.get("page", 1))
    size = int(payload.get("size", 25))

    q = db.query(model).filter(model.org_id == ctx["org_id"])
    q = apply_filters(q, model, filters)
    q = apply_sort(q, model, sort)
    total, rows = paginate(q, page=page, size=size)

    rec = RecentSearch(
        org_id=ctx["org_id"],
        user_id=user.id,
        entity=entity,
        query={"filters": filters, "sort": sort},
    )
    db.add(rec)
    db.commit()

    def to_dict(obj):
        if isinstance(obj, Legacy):
            return {"id": obj.id, "slug": obj.slug, "name": obj.name}
        if isinstance(obj, Deal):
            return {
                "id": obj.id,
                "status": obj.status,
                "city": obj.city,
                "state": obj.state,
                "price": str(obj.price) if obj.price is not None else None,
                "created_at": obj.created_at,
            }
        return {"id": getattr(obj, "id", None)}

    return {"total": total, "items": [to_dict(r) for r in rows], "page": page, "size": size}


@router.get("/views/{entity}")
def list_views(
    entity: str,
    ctx=Depends(org_membership()),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    rows = (
        db.query(SavedView)
        .filter(SavedView.org_id == ctx["org_id"])
        .filter((SavedView.user_id == user.id) | (SavedView.shared == True))
        .filter(SavedView.entity == entity)
        .order_by(SavedView.name.asc())
        .all()
    )
    return [{"id": r.id, "name": r.name, "shared": r.shared, "query": r.query} for r in rows]


@router.post("/views/{entity}")
def create_view(
    entity: str,
    payload: Dict[str, Any],
    ctx=Depends(org_membership()),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    v = SavedView(
        org_id=ctx["org_id"],
        user_id=user.id,
        entity=entity,
        name=payload["name"],
        query=payload.get("query", {}),
        shared=bool(payload.get("shared", False)),
    )
    db.add(v)
    db.commit()
    db.refresh(v)
    return {"id": v.id}


@router.patch("/views/{view_id}")
def update_view(
    view_id: int,
    payload: Dict[str, Any],
    ctx=Depends(org_membership()),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    v = (
        db.query(SavedView)
        .filter(SavedView.id == view_id, SavedView.org_id == ctx["org_id"])
        .first()
    )
    if not v:
        raise HTTPException(status_code=404, detail="Not found")
    if v.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not your view")
    for k in ["name", "query", "shared"]:
        if k in payload:
            setattr(v, k, payload[k])
    db.commit()
    return {"ok": True}


@router.delete("/views/{view_id}")
def delete_view(
    view_id: int,
    ctx=Depends(org_membership()),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    v = (
        db.query(SavedView)
        .filter(SavedView.id == view_id, SavedView.org_id == ctx["org_id"])
        .first()
    )
    if not v:
        raise HTTPException(status_code=404, detail="Not found")
    if v.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not your view")
    db.delete(v)
    db.commit()
    return {"ok": True}


@router.get("/recents/{entity}")
def list_recents(
    entity: str,
    limit: int = Query(10, ge=1, le=50),
    ctx=Depends(org_membership()),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    rows = (
        db.query(RecentSearch)
        .filter(
            RecentSearch.org_id == ctx["org_id"],
            RecentSearch.user_id == user.id,
            RecentSearch.entity == entity,
        )
        .order_by(RecentSearch.created_at.desc())
        .limit(limit)
        .all()
    )
    return [{"id": r.id, "query": r.query, "created_at": r.created_at} for r in rows]
