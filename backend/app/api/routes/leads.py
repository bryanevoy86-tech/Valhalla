from fastapi import APIRouter, Depends, File, Query, Response, UploadFile
from sqlalchemy.orm import Session

from ...crud import lead as crud_lead
from ...schemas import ImportResult
from ...schemas.lead import LeadCreate, LeadOut
from ...services import csv_utils
from ..deps import get_current_user, get_db

router = APIRouter(prefix="/leads", tags=["leads"])


@router.post("", response_model=LeadOut)
def create_lead(
    data: LeadCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return crud_lead.create(db, data, owner_id=user.id)


@router.get("", response_model=list[LeadOut])
def list_leads(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    _ = user  # auth gate only
    return crud_lead.list_all(db, limit, offset)


# --- CSV Export ---
@router.get("/export", response_class=Response)
def export_leads_csv(db: Session = Depends(get_db), user=Depends(get_current_user)):
    _ = user
    leads = crud_lead.list_all(db, limit=10000, offset=0)
    rows = [lead.model_dump() for lead in leads]
    headers = ["id", "name", "email", "phone", "created_at", "updated_at", "owner_id"]
    csv_text = csv_utils.to_csv(rows, headers)
    return Response(content=csv_text, media_type="text/csv")


# --- CSV Import ---
@router.post("/import", response_model=ImportResult)
async def import_leads_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    text = (await file.read()).decode()
    rows = csv_utils.from_csv(text)
    created = updated = skipped = errors = 0
    for row in rows:
        try:
            lead_in = LeadCreate(**row)
            # Try to find by email or phone
            existing = crud_lead.get_by_email_or_phone(db, lead_in.email, lead_in.phone)
            if existing:
                updated += 1
                crud_lead.update(db, existing.id, lead_in)
            else:
                created += 1
                crud_lead.create(db, lead_in, owner_id=user.id)
        except Exception:
            errors += 1
            skipped += 1
    return ImportResult(created=created, updated=updated, skipped=skipped, errors=errors)
