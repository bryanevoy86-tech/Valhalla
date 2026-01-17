from fastapi import APIRouter, Depends, File, Query, Response, UploadFile
from sqlalchemy.orm import Session

from ...crud import buyer as crud_buyer
from ...schemas import ImportResult
from ...schemas.buyer import BuyerCreate, BuyerOut
from ...services import csv_utils
from ...services.buyer_matcher import DealSearch, rank_buyers
from ..deps import get_current_user, get_db

router = APIRouter(prefix="/buyers", tags=["buyers"])


@router.post("", response_model=BuyerOut)
def create_buyer(data: BuyerCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    _ = user
    return crud_buyer.create(db, data)


@router.get("", response_model=list[BuyerOut])
def list_buyers(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    legacy_id: str | None = Query(None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    _ = user
    return crud_buyer.list_all(db, limit, offset, legacy_id)


# --- CSV Export ---
@router.get("/export", response_class=Response)
def export_buyers_csv(db: Session = Depends(get_db), user=Depends(get_current_user)):
    _ = user
    buyers = crud_buyer.list_all(db, limit=10000, offset=0)
    rows = [buyer.model_dump() for buyer in buyers]
    headers = [
        "id",
        "name",
        "email",
        "phone",
        "created_at",
        "updated_at",
        "legacy_id",
        "markets",
        "zips",
        "price_min",
        "price_max",
        "beds_min",
        "baths_min",
    ]
    csv_text = csv_utils.to_csv(rows, headers)
    return Response(content=csv_text, media_type="text/csv")


# --- CSV Import ---
@router.post("/import", response_model=ImportResult)
async def import_buyers_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    text = (await file.read()).decode()
    rows = csv_utils.from_csv(text)
    created = updated = skipped = errors = 0
    for row in rows:
        try:
            buyer_in = BuyerCreate(**row)
            # Try to find by email or phone
            existing = crud_buyer.get_by_email_or_phone(db, buyer_in.email, buyer_in.phone)
            if existing:
                updated += 1
                crud_buyer.update(db, existing.id, buyer_in)
            else:
                created += 1
                crud_buyer.create(db, buyer_in)
        except Exception:
            errors += 1
            skipped += 1
    return ImportResult(created=created, updated=updated, skipped=skipped, errors=errors)


@router.get("/match")
def match_buyers(
    price: float = Query(..., description="Asking price or expected purchase"),
    beds: float | None = Query(None),
    baths: float | None = Query(None),
    city: str | None = Query(None, description="Market/city string, matches buyer.markets"),
    zip: str | None = Query(None, description="Postal or zip code, matches buyer.zips"),
    property_type: str | None = Query(None, description="sfh, duplex, triplex, mfh, land"),
    tags: str | None = Query(None, description="Comma CSV like 'cash,quick-close'"),
    legacy_id: str | None = Query(None),
    limit: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    from ...models.buyer import Buyer

    _ = user
    buyers = db.query(Buyer).filter(Buyer.active == True).all()
    q = DealSearch(
        city=city,
        zip=zip,
        price=price,
        beds=beds,
        baths=baths,
        property_type=property_type,
        tags=set(t.strip().lower() for t in (tags or "").split(",") if t.strip()),
        legacy_id=legacy_id,
    )
    ranked = rank_buyers(buyers, q, top_k=limit)
    return [
        {
            "buyer": {
                "id": b.id,
                "name": b.name,
                "email": b.email,
                "phone": b.phone,
                "legacy_id": b.legacy_id,
                "markets": b.markets,
                "zips": b.zips,
                "price_min": b.price_min,
                "price_max": b.price_max,
                "beds_min": b.beds_min,
                "baths_min": b.baths_min,
                "property_types": b.property_types,
                "tags": b.tags,
                "active": b.active,
            },
            "score": s,
        }
        for (b, s) in ranked
    ]
