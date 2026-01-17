from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.docs import service, schemas
from app.core.engines.guard_runtime import enforce_engine
from app.core.engines.actions import CONTRACT_SEND

router = APIRouter(prefix="/docs", tags=["docs"])


@router.post("/templates", response_model=schemas.DocTemplateResponse)
def create_template(
    data: schemas.DocTemplateCreate,
    db: Session = Depends(get_db),
):
    return service.create_template(db, data)


@router.get("/templates", response_model=list[schemas.DocTemplateResponse])
def list_templates(db: Session = Depends(get_db)):
    return service.list_templates(db)


@router.post("/generate", response_model=schemas.GeneratedDocResponse)
def generate_doc(
    request: schemas.GenerateDocRequest,
    db: Session = Depends(get_db),
):
    return service.generate_document(db, request)


@router.get("/generated", response_model=list[schemas.GeneratedDocResponse])
def list_generated(db: Session = Depends(get_db)):
    return service.list_generated(db)


@router.post("/send")
def send_for_esign(
    request: schemas.SendForESignRequest,
    db: Session = Depends(get_db),
):
    enforce_engine("wholesaling", CONTRACT_SEND)
    return service.send_for_esign(db, request)
