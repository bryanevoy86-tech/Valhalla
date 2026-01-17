from fastapi import APIRouter

router = APIRouter(prefix="/funfund", tags=["funfund"])


@router.get("/health")
def health():
    return {"ok": True, "module": "funfund"}
