from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..core.db import get_db

router = APIRouter(prefix="/capital", tags=["capital"])


@router.post("/intake")
async def create_capital_intake(data: dict, db: Session = Depends(get_db)):
    return {"ok": True, "message": "Capital intake created"}


@router.get("/intake")
async def list_capital_intake(db: Session = Depends(get_db)):
    return {"intakes": []}
