from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.heimdall.services.buyer_csv_parser import (
    parse_buyer_csv,
)
from app.heimdall.services.buyer_import_service import (
    import_buyers,
)

router = APIRouter(
    prefix="/heimdall/buyers",
    tags=["Heimdall Buyers"],
)


@router.post("/upload")
async def upload_buyers(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    content = await file.read()
    parsed = parse_buyer_csv(
        content.decode("utf-8-sig")
    )
    imported = import_buyers(
        db=db,
        buyers=parsed.get("buyers", []),
    )

    return {
        "parsed": parsed,
        "imported": imported,
    }
