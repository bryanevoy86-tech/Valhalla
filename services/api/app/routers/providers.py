from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.providers.schemas import TokenCreate, TokenOut
from app.providers import service as svc
from app.providers.registry import ADAPTERS

router = APIRouter(prefix="/providers", tags=["providers"])


@router.get("/{provider}/health")
def provider_health(provider: str):
    adapter = ADAPTERS.get(provider)
    if not adapter:
        raise HTTPException(404, "Unknown provider")
    return adapter.health()


@router.post("/tokens", response_model=TokenOut)
def create_token(body: TokenCreate, db: Session = Depends(get_db)):
    # NOTE: encrypt access_token at app layer if not already
    tok = svc.save_token(db, **body.model_dump())
    return TokenOut(id=tok.id, provider=tok.provider, account_ref=tok.account_ref)


@router.get("/tokens", response_model=list[TokenOut])
def get_tokens(provider: str | None = None, db: Session = Depends(get_db)):
    toks = svc.list_tokens(db, provider)
    return [TokenOut(id=t.id, provider=t.provider, account_ref=t.account_ref) for t in toks]


@router.delete("/tokens/{token_id}")
def delete_token(token_id: int, db: Session = Depends(get_db)):
    ok = svc.delete_token(db, token_id)
    if not ok:
        raise HTTPException(404, "Not found")
    return {"ok": True}


@router.post("/{provider}/webhook")
async def provider_webhook(provider: str, request: Request, db: Session = Depends(get_db)):
    adapter = ADAPTERS.get(provider)
    if not adapter:
        raise HTTPException(404, "Unknown provider")
    body = await request.body()
    try:
        data = await request.json()
    except:
        data = {}
    signature = request.headers.get("X-Signature", None)
    if not adapter.validate_signature(body, signature):
        raise HTTPException(400, "Invalid signature")
    evt_type = data.get("event_type") or "unknown"
    evt = svc.record_webhook(db, provider, evt_type, data, signature)
    # TODO: dispatch to internal handlers (e.g., Stripe invoice.paid, DocuSign Completed)
    return {"ok": True, "event_id": evt.id}
