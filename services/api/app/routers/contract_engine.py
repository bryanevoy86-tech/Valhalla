from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

router = APIRouter(prefix="/contract", tags=["contract"])

class TemplateIn(BaseModel):
    name: str
    jurisdiction: str
    language: str = "en"
    structure: List[str]

class ContractCreate(BaseModel):
    deal_id: int
    template_id: int
    variables: Dict[str, Any]
    counterparty_email: str
    counterparty_name: str

@router.post("/template")
def create_template(payload: TemplateIn):
    return {"ok": True, "template_id": 100}

@router.get("/template/list")
def list_templates(jurisdiction: Optional[str] = None):
    return {"templates": []}

@router.post("/draft")
def draft_contract(payload: ContractCreate):
    return {"ok": True, "contract_id": 5001, "status": "draft"}

@router.post("/pdf/{contract_id}")
def build_pdf(contract_id: int):
    return {"ok": True, "pdf_url": f"s3://contracts/{contract_id}.pdf"}

@router.post("/send/{contract_id}")
def send_for_esign(contract_id: int):
    return {"ok": True, "status": "sent"}

@router.get("/status/{contract_id}")
def contract_status(contract_id: int):
    return {"contract_id": contract_id, "status": "sent", "signers": []}

@router.post("/webhook/esign")
def esign_webhook(event: Dict[str, Any]):
    return {"ok": True}
